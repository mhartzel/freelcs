package main

import (
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/wneessen/go-mail"
)

// Global constants and state
const heartbeat_checker_version = "400"
var debug = true

var (
	heartbeat_checker_pid                           int
	loudness_correction_program_info_and_timestamps map[string]interface{}
	report_lock                                     sync.RWMutex
	all_settings_dict                               map[string]interface{}
	quit_all_threads_now                            bool = false

	// Default Settings
	silent_mode                         bool     = false
	heartbeat_check_interval            int      = 120
	use_tls                             bool     = false
	smtp_server_requires_authentication bool     = false
	smtp_username                       string   = "firstname.lastname@company.com"
	smtp_password                       string   = "password"
	smtp_server_name                    string   = "smtp.company.com"
	smtp_server_port                    int      = 25
	message_recipients                  []string = []string{"recipient1@company.com", "recipient2@company.com"}
	message_title                       string   = "LoudnessCorrection Error Message"
	message_attachment_path             string   = ""

	// Dynamic program info extracted from heartbeats
	loudness_correction_commandline []string
	loudness_correction_pid         interface{}
	all_ip_addresses_of_the_machine []string
	freelcs_version                 string = "Not known yet"
	loudnesscorrection_version      string = "Not known yet"
)

// --- Helper Functions ---

func parse_time_to_string(time_int int64) string {

	time_object := time.Unix(time_int, 0)
	// Format: YYYY.MM.DD at HH:MM:SS
	return time_object.Format("2006.01.02 at 15:04:05")
}

func send_error_email(recipients []string, title string, body_text string, attachment_path string) {

	program_info := fmt.Sprintf(
		"\nFreeLCS version: %s\n\n\nLoudnessCorrection info:\n--------------------------------------\n"+
			"Commandline: %s\nIP-Addresses: %s\nPID: %v\nLoudnessCorrection version: %s\n\n"+
			"HeartBeat Checker info:\n--------------------------------------\n"+
			"Commandline: %s\nPID: %d\nHeartBeat Checker version: %s\n\n",
		freelcs_version,
		strings.Join(loudness_correction_commandline, " "),
		strings.Join(all_ip_addresses_of_the_machine, ", "),
		loudness_correction_pid,
		loudnesscorrection_version,
		strings.Join(os.Args, " "),
		heartbeat_checker_pid,
		heartbeat_checker_version,
	)

	if debug == true {

		fmt.Println("smtp_username:", smtp_username)
		fmt.Println("smtp_password:", smtp_password)
		fmt.Printf("Recipients: ")

		for _, email_address := range recipients {
			fmt.Printf(email_address + ", ")
		}

		fmt.Println("title:", title)
		fmt.Println("body_text:", body_text)
		fmt.Println("program_info:", program_info)
		fmt.Println("smtp_server_name:", smtp_server_name)
		fmt.Println("smtp_server_port:", smtp_server_port)
		fmt.Println()
	}

	message := mail.NewMsg()

	if err := message.From(smtp_username); err != nil {
		log.Printf("Error setting sender: %v", err)
		return
	}

	if err := message.To(recipients...); err != nil {
		log.Printf("Error setting recipients: %v", err)
		return
	}


	message.Subject(title)
	message.SetBodyString(mail.TypeTextPlain, body_text + program_info)

	if attachment_path != "" {
		message.AttachFile(attachment_path)
	}

	// Configure client
	client_options := []mail.Option{
		mail.WithPort(smtp_server_port),
		mail.WithSMTPAuth(mail.SMTPAuthAutoDiscover),
		mail.WithUsername(smtp_username),
		mail.WithPassword(smtp_password),
	}

	if use_tls {
		client_options = append(client_options, mail.WithTLSPolicy(mail.TLSMandatory))
	} else {
		client_options = append(client_options, mail.WithTLSPolicy(mail.NoTLS))
	}

	mail_client, err := mail.NewClient(smtp_server_name, client_options...)

	if err != nil {
		log.Printf("Error creating mail client: %v", err)
		return
	}

	if err := mail_client.DialAndSend(message); err != nil {
		log.Printf("Failed to send email: %v", err)
	} else if !silent_mode {
		log.Printf("Sent email to: %v", recipients)
	}
}

// --- Middleware ---

func limit_request_body_size(max_bytes int64) gin.HandlerFunc {

	return func(context *gin.Context) {
		context.Request.Body = http.MaxBytesReader(context.Writer, context.Request.Body, max_bytes)
		context.Next()
	}
}

// --- Route Handlers ---

func handle_receive_heartbeat(context *gin.Context) {

	var incoming_payload map[string]interface{}

	if err := context.ShouldBindJSON(&incoming_payload); err != nil {
		context.JSON(http.StatusBadRequest, gin.H{"error": "Invalid JSON payload"})
		return
	}

	// Security: Constant-time comparison to prevent timing attacks
	incoming_auth, _ := incoming_payload["authorization"].(string)
	expected_auth, _ := all_settings_dict["authorization"].(string)

	if subtle.ConstantTimeCompare([]byte(incoming_auth), []byte(expected_auth)) != 1 {
		context.JSON(http.StatusUnauthorized, gin.H{"error": "Unauthorized access"})
		return
	}

	sanitized_payload := make(map[string]interface{})

	for key, value := range incoming_payload {
		// Basic length check for values to avoid large string attacks
		if len(fmt.Sprintf("%v", value)) < 1024 {

			sanitized_payload[key] = value

			if debug == true {
				fmt.Println("value:", value)
			}
		}
	}

	if debug == true {
		fmt.Println()
		fmt.Println("incoming_auth:", incoming_auth)
		fmt.Println("expected_auth:", expected_auth)
		fmt.Println("sanitized_payload:")
		fmt.Println(sanitized_payload)
		fmt.Println()
	}

	report_lock.Lock()
	loudness_correction_program_info_and_timestamps = sanitized_payload
	report_lock.Unlock()

	context.JSON(http.StatusOK, gin.H{"status": "success"})
}

// --- Background Worker ---

func check_timestamps_loop() {

	previous_timestamps := make(map[string]interface{})
	startup_message_sent := false
	alert_email_sent := false

	for {
		if quit_all_threads_now {
			return
		}

		time.Sleep(time.Duration(heartbeat_check_interval) * time.Second)

		report_lock.RLock()

		// Replicate Python data extraction
		if prog_info, ok := loudness_correction_program_info_and_timestamps["loudnesscorrection_program_info"].([]interface{}); ok && len(prog_info) >= 5 {

			if cmd_list, ok := prog_info[0].([]interface{}); ok {
				loudness_correction_commandline = nil
				for _, cmd := range cmd_list {
					loudness_correction_commandline = append(loudness_correction_commandline, fmt.Sprint(cmd))
				}
			}

			loudness_correction_pid = prog_info[1]

			if ip_list, ok := prog_info[2].([]interface{}); ok {
				all_ip_addresses_of_the_machine = nil
				for _, ip := range ip_list {
					all_ip_addresses_of_the_machine = append(all_ip_addresses_of_the_machine, fmt.Sprint(ip))
				}
			}

			freelcs_version = fmt.Sprint(prog_info[3])
			loudnesscorrection_version = fmt.Sprint(prog_info[4])
		}

		current_data := loudness_correction_program_info_and_timestamps
		report_lock.RUnlock()

		if debug == true {
			fmt.Println()
			fmt.Println("time.Now().Unix()):", time.Now().Unix())
		}

		current_time_string := parse_time_to_string(time.Now().Unix())

		if debug == true {
			fmt.Println("current_time_string:", current_time_string)
			fmt.Println()
		}

		if !startup_message_sent {
			startup_message_sent = true
			msg := "HeartBeat_Checker started: " + current_time_string + "\n\n"
			send_error_email(message_recipients, "HeartBeat_Checker has started.", msg, message_attachment_path)
		}

		if len(previous_timestamps) == 0 {
			previous_timestamps = current_data
			continue
		}

		stopped_threads_counter := 0
		var error_messages []string

		for key, value := range current_data {

			if debug == true {
				fmt.Println()
				fmt.Println("key:", key)
				fmt.Println("value:", value)
				fmt.Println()
			}

			if key == "loudnesscorrection_program_info" || key == "authorization" {
				continue
			}

			details, ok := value.([]interface{})

			if !ok || len(details) < 2 {
				continue
			}

			// details[0] is the boolean 'enabled' flag
			if enabled, ok := details[0].(bool); ok && !enabled {
				continue
			}

			// Compare current timestamp to previous timestamp
			prev_val, prev_exists := previous_timestamps[key].([]interface{})

			if prev_exists && len(prev_val) >= 2 {

				// We compare the timestamps (index 1) as strings to handle various numeric types from JSON
				if fmt.Sprintf("%v", details[1]) == fmt.Sprintf("%v", prev_val[1]) {
					stopped_threads_counter++
					ts_int := int64(0)

					// FIXME

					// if ts_int, ok := details[1].(int64); ok {
					// 	ts_int = int64(ts_int)
					// }

					if ts_int, ok := prev_val[1].(int64); ok {
						ts_int = int64(ts_int)
					}

					if debug == true {
						fmt.Println()
						fmt.Println("ts_int", ts_int)
					}

					ts_str := parse_time_to_string(ts_int)

					if debug == true {
						fmt.Println()
						fmt.Println("ts_str", ts_str)
					}

					msg := fmt.Sprintf("LoudnessCorrection has stopped updating '%s' timestamps. Last update: %s", key, ts_str)
					error_messages = append(error_messages, msg)

					if debug == true {
						fmt.Println()
						fmt.Println("details:", details)
						fmt.Println("prev_val:", prev_val)
						fmt.Println()
						fmt.Println()
					}
				}
			}
		}

		if stopped_threads_counter > 0 {

			if !alert_email_sent {

				if !silent_mode {

					for _, line := range error_messages {
						fmt.Println(line)
					}
				}

				body := strings.Join(error_messages, "\n")
				send_error_email(message_recipients, message_title, body, message_attachment_path)
				alert_email_sent = true
			}
		} else if alert_email_sent {
			// Reset if threads resumed
			alert_email_sent = false
			msg := "All Heartbeat timestamps started updating again at: " + current_time_string + "\n\n"
			send_error_email(message_recipients, message_title, msg, message_attachment_path)
		}

		previous_timestamps = current_data
	}
}

// --- Main ---

func main() {

	heartbeat_checker_pid = os.Getpid()

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
		fmt.Println("")
		fmt.Println("")
	}

	file_bytes, err := os.ReadFile(json_path)

	if err != nil {
		log.Fatalf("Error reading configfile: %v", err)
	}

	if err := json.Unmarshal(file_bytes, &all_settings_dict); err != nil {
		log.Fatalf("Error parsing JSON config: %v", err)
	}

	// Load settings from config
	if val, ok := all_settings_dict["silent"].(bool); ok {
		silent_mode = val
	}

	if val, ok := all_settings_dict["heartbeat_write_interval"].(int); ok {
		heartbeat_check_interval = int(val) * 4
	}

	if email_details, ok := all_settings_dict["email_sending_details"].(map[string]interface{}); ok {
		use_tls, _ = email_details["use_tls"].(bool)
		smtp_server_requires_authentication, _ = email_details["smtp_server_requires_authentication"].(bool)
		smtp_username, _ = email_details["smtp_username"].(string)
		smtp_password, _ = email_details["smtp_password"].(string)
		smtp_server_name, _ = email_details["smtp_server_name"].(string)

		// if smtp_port, ok := email_details["smtp_server_port"].(string); ok {
		// 	smtp_server_port = strconv.Atoi(smtp_port)
		// }

		if smtp_port, err := strconv.Atoi(email_details["smtp_server_port"].(string)); err == nil {
			smtp_server_port = smtp_port
		}

		if recs, ok := email_details["message_recipients"].([]interface{}); ok {
			message_recipients = nil
			for _, r := range recs {
				message_recipients = append(message_recipients, fmt.Sprint(r))
			}
		}

		message_title, _ = email_details["message_title"].(string)
	}

	if debug == true {
		fmt.Println()
		fmt.Println("use_tls:", use_tls)
		fmt.Println("smtp_server_requires_authentication:", smtp_server_requires_authentication)
		fmt.Println("smtp_username:", smtp_username)
		fmt.Println("smtp_password:", smtp_password)
		fmt.Println("smtp_server_name:", smtp_server_name)
		fmt.Println("smtp_server_port:", smtp_server_port)
		fmt.Println()
	}

	// Start monitoring thread
	go check_timestamps_loop()

	// Initialize Gin
	gin.SetMode(gin.ReleaseMode)
	router := gin.Default()

	// Add Security Middleware: Max Content Length 100KB
	router.Use(limit_request_body_size(1024 * 100))

	router.POST("/heartbeat", handle_receive_heartbeat)

	port := "8080"

	if p, ok := all_settings_dict["heartbeat_service_port"].(string); ok {
		port = p
	}

	fmt.Printf("Starting HeartBeat Checker on port %s...\n", port)

	if err := router.Run(":" + port); err != nil {
		log.Fatalf("Server failed: %v", err)
	}

	quit_all_threads_now = true
}


