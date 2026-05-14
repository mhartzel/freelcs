package main

import (
	"crypto/subtle"
	"encoding/json"
	"html/template"
	"log"
	"net/http"
	"os"
	"sync"
	"github.com/gin-gonic/gin"
	"github.com/gin-gonic/gin/binding"
	"fmt"
	"strings"
	"path/filepath"
)

// Global variable definitions
var default_settings map[string]interface{} // Key = string and value needs to be interface since values can be int or string.
var progress_report_data  = make(map[string][]string)
var progress_report_mutex     sync.RWMutex
var version = "400"
var debug = false

const html_template = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="5">
    <title>FreeLCS Progress Report</title>
    <style>
        body { font-family: monospace; padding: 20px; background: #1a1a1a; color: #00ff00; }
        .box { border: 1px solid #444; padding: 15px; background: #222; margin: 15px 0; }
        h1, h2 { color: #fff; }
        hr { border: 0; border-top: 1px solid #444; }
        p { color: #aaaaaa; }
    </style>
</head>
<body>
    <h1>{{.title_1}}</h1>
    <p>{{.realtime}}</p>
    <h2>{{.title_2}}</h2><hr>
    {{range .files_waiting_in_queue}}<div>{{.}}</div>{{end}}
    <div class="box">
        <h2>{{.title_3}}</h2><hr>
        {{range .files_being_processed}}<div>{{.}}</div>{{end}}
    </div>
    <h2>{{.title_4}}</h2><hr>
    {{range .processed_files}}<div>{{.}}</div>{{end}}
</body>
</html>
`

func authorize_and_sanitize_input_data(context *gin.Context) {

	// Get autorization key from incoming data and if it is accepted accept other data in the incoming message

	// Limit request body to 500 KB to prevent Memory Exhaustion
	context.Request.Body = http.MaxBytesReader(context.Writer, context.Request.Body, 500 * 1024)

	// AuthorizationData defines exactly what we accept.
	// Any extra keys sent by an attacker are automatically discarded.
	// This datatype is only used for filtering the authorization key from the incoming data.
	type AuthorizationData struct {
		Authorization string            `json:"authorization"`
		Data          map[string]string `json:"-"` // We won't map everything to a flat structure
	}

	type ReportData struct {
		Title_1          []string `json:"title_1"`
		Title_2          []string `json:"title_2"`
		Title_3          []string `json:"title_3"`
		Title_4          []string `json:"title_4"`
		Queued_Files     []string `json:"files_waiting_in_queue"`
		Processing_Files []string `json:"files_being_processed"`
		Processed_Files  []string `json:"processed_files"`
		Realtime         []string `json:"realtime"`
	}

	// Get only the authorization code from the incoming json. The AuthorizationData struct does the filtering.
	// This way we won't read in other json data if authorization fails.
	incoming_authorization_data := AuthorizationData{}

	if err := context.ShouldBindBodyWith(&incoming_authorization_data, binding.JSON); err != nil {
		context.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	// Constant-Time Comparison against Timing Attacks
	incomingAuth := incoming_authorization_data.Authorization
	expectedAuth, _ := default_settings["authorization"].(string)

	// subtle.ConstantTimeCompare prevents Timing Attacks by
	// ensuring the comparison always takes the same amount of time.
	if subtle.ConstantTimeCompare([]byte(incomingAuth), []byte(expectedAuth)) != 1 {
		context.AbortWithStatusJSON(http.StatusUnauthorized, gin.H{"error": "Access denied"})
		return
	}

	if debug == true {
		fmt.Println("")
		fmt.Println("incomingAuth:", incomingAuth)
		fmt.Println("expectedAuth:", expectedAuth)
		fmt.Println("")
	}

	// Read incoming data again and insert into incoming_json_as_map
	incoming_json_as_map := ReportData{}

	if err := context.ShouldBindBodyWith(&incoming_json_as_map, binding.JSON); err != nil {
		context.AbortWithStatusJSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}

	if debug == true {
		fmt.Println("incoming_json_as_map:")
		fmt.Println(incoming_json_as_map)
		fmt.Println("")
	}

	var sanitized_queued_files []string
	var sanitized_processed_files []string
	var sanitized_completed_files []string

	// Filter and Sanitize input (convert all incoming data to strings).
	// We manually move only valid string data into our global map
	list_of_filenames := incoming_json_as_map.Queued_Files

	// Sanity check for the length of filenames coming in
	if len(list_of_filenames) > 200 { return }

	for _,filename := range list_of_filenames {
		if len(string(filename)) < 200 {
			sanitized_queued_files = append(sanitized_queued_files, string(filename))
		}
	}

	list_of_filenames = incoming_json_as_map.Processing_Files

	// Sanity check for the length of filenames coming in
	if len(list_of_filenames) > 200 { return }

	for _,filename := range list_of_filenames {
		if len(string(filename)) < 200 {
			sanitized_processed_files = append(sanitized_processed_files, string(filename))
		}
	}

	list_of_filenames = incoming_json_as_map.Processed_Files

	// Sanity check for the length of filenames coming in
	if len(list_of_filenames) > 200 { return }

	for _,filename := range list_of_filenames {
		if len(string(filename)) < 200 {
			sanitized_completed_files = append(sanitized_completed_files, string(filename))
		}
	}

	// Get mutex lock for modifying the global map that is also accessed in other threads
	progress_report_mutex.Lock()
		var temp_slice_of_strings []string
		progress_report_data["files_waiting_in_queue"] = sanitized_queued_files
		progress_report_data["files_being_processed"] = sanitized_processed_files
		progress_report_data["processed_files"] = sanitized_completed_files

		if len(incoming_json_as_map.Title_1) > 0 {
			temp_slice_of_strings = incoming_json_as_map.Title_1
			progress_report_data["title_1"] = temp_slice_of_strings
		}

		temp_slice_of_strings = nil

		if len(incoming_json_as_map.Title_2) > 0 {
			temp_slice_of_strings = incoming_json_as_map.Title_2
			progress_report_data["title_2"] = temp_slice_of_strings
		}

		temp_slice_of_strings = nil

		if len(incoming_json_as_map.Title_3) > 0 {
			temp_slice_of_strings = incoming_json_as_map.Title_3
			progress_report_data["title_3"] = temp_slice_of_strings
		}

		temp_slice_of_strings = nil

		if len(incoming_json_as_map.Title_4) > 0 {
			temp_slice_of_strings = incoming_json_as_map.Title_4
			progress_report_data["title_4"] = temp_slice_of_strings
		}

		temp_slice_of_strings = nil

		if len(incoming_json_as_map.Realtime) > 0 {
			temp_slice_of_strings = incoming_json_as_map.Realtime
			progress_report_data["realtime"] = temp_slice_of_strings
		}

	progress_report_mutex.Unlock()

	if debug == true {
		fmt.Println("progress_report_data:")
		fmt.Println(progress_report_data)
		fmt.Println("")
	}

	context.JSON(http.StatusOK, gin.H{"status": "updated"})
}

func render_progress_report(context *gin.Context) {

	// Get mutex Read lock for reading the global map. With this lock it can be read also in other threads simultaneously
	progress_report_mutex.RLock()
	defer progress_report_mutex.RUnlock()

	context.HTML(http.StatusOK, "progress_report", gin.H{
		"files_waiting_in_queue":     progress_report_data["files_waiting_in_queue"],
		"files_being_processed": progress_report_data["files_being_processed"],
		"processed_files":     progress_report_data["processed_files"],
	})
}

func main() {

	// Handle commandline options
	if len(os.Args) != 3 || strings.ToLower(os.Args[1]) != "-configfile" {
		fmt.Println("\nUSAGE: Give the option: -configfile followed by full path to the config file.")
		os.Exit(1)
	}

	config_path := os.Args[2]
	json_path := strings.TrimSuffix(config_path, filepath.Ext(config_path)) + ".json"

	if debug == true {
		fmt.Println("")
		fmt.Println("os.Args[0]:", os.Args[0])
		fmt.Println("os.Args[1]:", os.Args[1])
		fmt.Println("os.Args[2]:", os.Args[2])
		fmt.Println("json_path:", json_path)
		fmt.Println("")
	}

	// Read configuration from common config - file
	file_bytes, err := os.ReadFile(json_path)

	if err != nil {
		log.Fatalf("Error reading configfile: %v", err)
	}

	// Convert config - file json to a map
	if err := json.Unmarshal(file_bytes, &default_settings); err != nil {
		log.Fatalf("Error parsing JSON config: %v", err)
	}

	if err != nil {
		log.Fatalf("Cannot load settings: %v", err)
	}

	var server_incoming_port = "9000"
	var server_incoming_path = "/progress_report"

	gin.SetMode(gin.ReleaseMode) // Set Gin to production / release mode as opposed to rehearse
	gin_instance := gin.New() // gin.New() is cleaner than Default() for secure apps
	gin_instance.Use(gin.Recovery()) // Use the recovery middleware to catch unexpected errors, panic when error occurs

	// Create a new template based on definition in variable: html_template
	progress_report_template := template.Must(template.New("progress_report").Parse(html_template))

	// Create a new gin instance
	gin_instance.SetHTMLTemplate(progress_report_template)

	// Create a path for receiving progress report data through REST - api
	// Register path /progress_report for the POST - method
	if _, ok := default_settings["progress_service_path"]; ok {
		server_incoming_path = default_settings["progress_service_path"].(string)
	}

	gin_instance.POST(server_incoming_path, authorize_and_sanitize_input_data)

	// Create a path for serving a web - page
	// Register path / for the GET - method
	gin_instance.GET("/", func(context *gin.Context) {

		// Get mutex Read lock for reading the global map. With this lock it can be read also in other threads simultaneously
		progress_report_mutex.RLock()
		defer progress_report_mutex.RUnlock()

		// Render HTML page inserting text from variables into HTML template
		// The code below calls funciongetSortedValues that returns a list that is inserted
		// as the value into the map. Keys of the map are: queue, processed, ready.
		title_1 := ""
		title_2 := ""
		title_3 := ""
		title_4 := ""
		realtime := ""

		temp_slice := progress_report_data["title_1"]

		if len(temp_slice) > 0 {
			title_1 = temp_slice[0]
		} else {
			title_1 = "FreeLCS Progress Report"
		}

		temp_slice = progress_report_data["title_2"]

		if len(temp_slice) > 0 {
			title_2 = temp_slice[0]
		} else {
			title_2 = "0 Files Waiting In The Queue"
		}

		temp_slice = progress_report_data["title_3"]

		if len(temp_slice) > 0 {
			title_3 = temp_slice[0]
		} else {
			title_3 = "Files Being Processed"
		}

		temp_slice = progress_report_data["title_4"]

		if len(temp_slice) > 0 {
			title_4 = temp_slice[0]
		} else {
			title_4 = "Completed Files"
		}

		temp_slice = progress_report_data["realtime"]

		if len(temp_slice) > 0 {
			realtime = temp_slice[0]
		} else {
			realtime = ""
		}

		context.HTML(http.StatusOK, "progress_report", gin.H{
			"title_1": title_1,
			"title_2": title_2,
			"title_3": title_3,
			"title_4": title_4,
			"realtime": realtime,
			"files_waiting_in_queue":     progress_report_data["files_waiting_in_queue"],
			"files_being_processed": progress_report_data["files_being_processed"],
			"processed_files":     progress_report_data["processed_files"],
		})
	})

	if _, ok := default_settings["progress_service_port"]; ok {
		server_incoming_port = default_settings["progress_service_port"].(string)
	}

	log.Println("Starting ProgressReport on port ", server_incoming_port)

	if err := gin_instance.Run(":" + server_incoming_port) ; err != nil {
		log.Fatalf("Server failed to start: %v", err)
	}
}


