package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"html/template"
	"log"
	"net/http"
	"os"
	"sync"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
)

// Global variable definitions
var default_settings map[string]interface{} // Key = string and value needs to be interface since values can be int or string.
var progress_report_data  map[string]string
var progress_report_mutex     sync.RWMutex
var path_to_loudness_correction_settings_json = "/etc/Loudness_Correction_Settings.json"
var version = "400"

const html_template = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <title>FreeLCS Hardened Dashboard</title>
    <style>
        body { font-family: monospace; padding: 20px; background: #1a1a1a; color: #00ff00; }
        .box { border: 1px solid #444; padding: 15px; background: #222; margin: 15px 0; }
        h1, h2 { color: #fff; }
        hr { border: 0; border-top: 1px solid #444; }
    </style>
</head>
<body>
    <h1>FreeLCS Processing Report</h1>
    <p>Server: 192.168.2.50</p>
    <h2>Queue</h2><hr>
    {{range .queue}}<div>{{.}}</div>{{end}}
    <div class="box">
        <h2>Processing</h2><hr>
        {{range .processed}}<div>{{.}}</div>{{end}}
    </div>
    <h2>Completed</h2><hr>
    {{range .ready}}<div>{{.}}</div>{{end}}
</body>
</html>
`
func read_loudness_correction_settings_json(path string) {

	// Read common settings for all HeartBeat_Checker, LoudnesCorrection and Progress_Report from a json from disk,

	file, err := os.ReadFile(path)

	if err != nil {
		log.Fatalf("Cannot load settings: %v", err)
	}
	if err := json.Unmarshal(file, &default_settings); err != nil {
		log.Fatalf("JSON Error: %v", err)
	}
}

func authorize_and_sanitize_input_data(context *gin.Context) {

	// Get autorization key from incoming data and if it is accepted accept other data in the incoming message

	var incoming_json_as_map map[string]interface{}

	// Limit request body to 100 KB to prevent Memory Exhaustion
	context.Request.Body = http.MaxBytesReader(context.Writer, context.Request.Body, 100 * 1024)

	// ReportData defines exactly what we accept.
	// Any extra keys sent by an attacker are automatically discarded.
	// This datatype is only used for filtering the authorization key from the incoming data.
	type ReportData struct {
		Authorization string            `json:"authorization"`
		Data          map[string]string `json:"-"` // We won't map everything to a flat structure
	}

	// Get only the authorization code from the incoming json. The ReportData struct does the filtering.
	// This way we won't read in other json data if authorization fails.
	incoming_data := ReportData{}

	if err := context.ShouldBindBodyWith(&incoming_data, binding.JSON); err != nil {
		context.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// Constant-Time Comparison against Timing Attacks
	incomingAuth := incoming_data.Authorization
	expectedAuth, _ := default_settings["authorization"].(string)

	// subtle.ConstantTimeCompare prevents Timing Attacks by
	// ensuring the comparison always takes the same amount of time.
	if subtle.ConstantTimeCompare([]byte(incomingAuth), []byte(expectedAuth)) != 1 {
		context.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Access denied"})
		return
	}

	// Read incoming data again and insert into incoming_json_as_map
	if err := context.ShouldBindBodyWith(&incoming_json_as_map, binding.JSON); err != nil {
		context.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	// Filter and Sanitize input (convert all incoming data to strings).
	// We manually move only valid string data into our global map
	sanitized_incoming_data := make(map[string]string)

	for key, incoming_map_value := range incoming_json_as_map {
		if accepted_value, ok := incoming_map_value.(string); ok && len(accepted_value) < 1024 {
			sanitized_incoming_data[key] = accepted_value
		}
	}

	// Get mutex lock for modifying the global map that is also accessed in other threads
	progress_report_mutex.Lock()
	progress_report_data = sanitized_incoming_data
	progress_report_mutex.Unlock()

	context.JSON(http.StatusOK, gin.H{"status": "updated"})
}

func get_sorted_values(suffix string, count int) []string {

	var result []string

	for i := 1; i <= count; i++ {
		key := fmt.Sprintf("file_%d_%s", i, suffix)

		if val, ok := progress_report_data[key]; ok {
			result = append(result, val)
		}
	}

	return result
}

func render_progress_report(context *gin.Context) {

	// Get mutex Read lock for reading the global map. With this lock it can be read also in other threads simultaneously
	progress_report_mutex.RLock()
	defer progress_report_mutex.RUnlock()

	// The code below calls funciongetSortedValues that returns a list that is inserted
	// as the value into the map. Keys of the map are: queue, processed, ready.
	context.HTML(http.StatusOK, "progress_report", gin.H{
		"queue":     get_sorted_values("in_queue", 10),
		"processed": get_sorted_values("being_processed", 10),
		"ready":     get_sorted_values("ready", 50),
	})
}

func main() {

	progress_report_data = make(map[string]string)
	read_loudness_correction_settings_json(path_to_loudness_correction_settings_json)

	gin.SetMode(gin.ReleaseMode) // Set Gin to production / release mode as opposed to rehearse
	gin_instance := gin.New() // gin.New() is cleaner than Default() for secure apps
	gin_instance.Use(gin.Recovery()) // Use the recovery middleware to catch unexpected errors, panic when error occurs

	// Create a new template based on definition in variable: html_template
	progress_report_template := template.Must(template.New("progress_report").Parse(html_template))

	// Create a new gin instance
	gin_instance.SetHTMLTemplate(progress_report_template)

	// Create a path for receiving progress report data through REST - api
	// Register path /progress_report for the POST - method
	gin_instance.POST("/progress_report", authorize_and_sanitize_input_data)

	// Create a path for serving a web - page
	// Register path / for the GET - method
	gin_instance.GET("/", func(context *gin.Context) {

		// Get mutex Read lock for reading the global map. With this lock it can be read also in other threads simultaneously
		progress_report_mutex.RLock()
		defer progress_report_mutex.RUnlock()

		// Render HTML page inserting text from variables into HTML template
		// The code below calls funciongetSortedValues that returns a list that is inserted
		// as the value into the map. Keys of the map are: queue, processed, ready.
		context.HTML(http.StatusOK, "progress_report", gin.H{
			"queue":     get_sorted_values("in_queue", 10),
			"processed": get_sorted_values("being_processed", 10),
			"ready":     get_sorted_values("ready", 50),
		})
	})

	server_incoming_port := ":" + default_settings["progress_service_port"].(string)
	log.Println("Server running on", server_incoming_port)
	gin_instance.Run(server_incoming_port)
}


