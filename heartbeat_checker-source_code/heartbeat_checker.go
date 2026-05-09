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
var debug = false

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
	loudness_correction_commandline = ""
	heartbeat_checker_commandline = ""
	loudness_correction_pid =""
	all_ip_addresses_of_the_machine string
	freelcs_version                 string = "Not known yet"
	loudnesscorrection_version      string = "Not known yet"
)

// --- Helper Functions ---

func parse_time_to_string(time_string string) string {

	var time_int int64

	time_int, _ = strconv.ParseInt(time_string, 10, 64) 
	time_object := time.Unix(time_int, 0)

	// Format: YYYY.MM.DD at HH:MM:SS
	return time_object.Format("2006.01.02 at 15:04:05")
}

func send_error_email(recipients []string, title string, body_text string, attachment_path string) {

	program_info := fmt.Sprintf(
		"\nFreeLCS version: %s\n\n\n" +
		"LoudnessCorrection info:\n" +
		"--------------------------------------\n"+
		"Commandline: %s\n" +
		"IP-Addresses: %s\n" +
		"PID: %s\n" +
		"LoudnessCorrection version: %s\n\n"+
		"HeartBeat Checker info:\n" +
		"--------------------------------------\n"+
		"Commandline: %s\n" +
		"PID: %d\n" +
		"HeartBeat Checker version: %s\n\n",
		freelcs_version,
		loudness_correction_commandline,
		all_ip_addresses_of_the_machine,
		loudness_correction_pid,
		loudnesscorrection_version,
		heartbeat_checker_commandline,
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
	} else if silent_mode == false {
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

	if debug == true {

		fmt.Println()
		fmt.Println("incoming_payload:", incoming_payload)
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

	
	if debug == true {

		fmt.Println("loudness_correction_program_info_and_timestamps:", loudness_correction_program_info_and_timestamps)
		fmt.Println()
	}


	context.JSON(http.StatusOK, gin.H{"status": "success"})
}

// --- Background Worker ---

func check_timestamps_loop() {

	previous_timestamps := make(map[string]interface{})
	startup_message_has_been_sent := false
	alert_email_sent := false
	main_thread_heartbeat_enabled := false
	progress_report_thread_heartbeat_enabled := false
	main_thread_timestamp := "0"
	progress_report_thread_timestamp := "0"
	previous_main_thread_timestamp := "0"
	previous_progress_report_thread_timestamp := "0"

	for {
		if quit_all_threads_now == true {
			return
		}

		// Sleep between checking heartbeat timestamps
		time.Sleep(time.Duration(heartbeat_check_interval) * time.Second)

		// Get information we will send as the body of the error email
		report_lock.RLock()

			current_time_string := parse_time_to_string(strconv.FormatInt(time.Now().Unix(), 10))

			if debug == true {
				fmt.Println("current_time_string:", current_time_string)
				fmt.Println()
			}

			if incoming_value, ok := loudness_correction_program_info_and_timestamps["commandline"].(string); ok == true {
				loudness_correction_commandline = incoming_value

			}

			if incoming_value,ok := loudness_correction_program_info_and_timestamps["loudness_correction_pid"].(string) ; ok == true {
				loudness_correction_pid = incoming_value
			}

			if incoming_value,ok := loudness_correction_program_info_and_timestamps["all_ip_addresses_of_the_machine"].(string) ; ok == true {
				all_ip_addresses_of_the_machine = incoming_value
			}

			if incoming_value,ok := loudness_correction_program_info_and_timestamps["freelcs_version"].(string) ; ok == true {
				freelcs_version = incoming_value
			}

			if incoming_value,ok := loudness_correction_program_info_and_timestamps["loudnesscorrection_version"].(string) ; ok == true {
				loudnesscorrection_version = incoming_value
			}

			if debug == true {
				fmt.Println()
				fmt.Println("time.Now().Unix()):", time.Now().Unix())
			}

			// On first run send a message that the Heartbeat_Checker is running now
			if startup_message_has_been_sent == false {
				startup_message_has_been_sent = true
				message := "HeartBeat_Checker started: " + current_time_string + "\n\n"
				send_error_email(message_recipients, "HeartBeat_Checker has started.", message, message_attachment_path)
			}

			// Check if main_thread or write_html_progress_report - thread timestamps have stopped updating
			stopped_threads_counter := 0
			var error_messages []string

			if temp_list, ok := loudness_correction_program_info_and_timestamps["main_thread"].([]interface{}); ok == true {
				main_thread_heartbeat_enabled = temp_list[0].(bool)
				main_thread_timestamp = temp_list[1].(string)

			}

			if temp_list, ok := loudness_correction_program_info_and_timestamps["write_html_progress_report"].([]interface{}); ok == true {
				progress_report_thread_heartbeat_enabled = temp_list[0].(bool)
				progress_report_thread_timestamp = temp_list[1].(string)

			}

			if debug == true {
				fmt.Println()
				fmt.Println("main_thread_heartbeat_enabled:", main_thread_heartbeat_enabled)
				fmt.Println("main_thread_timestamp:", main_thread_timestamp)
				fmt.Println("progress_report_thread_heartbeat_enabled:", progress_report_thread_heartbeat_enabled)
				fmt.Println("progress_report_thread_timestamp:", progress_report_thread_timestamp)
				fmt.Println()
			}

			if temp_list, ok := previous_timestamps["main_thread"].([]interface{}); ok == true {
				previous_main_thread_timestamp = temp_list[1].(string)

			}

			if temp_list, ok := previous_timestamps["write_html_progress_report"].([]interface{}); ok == true {
				previous_progress_report_thread_timestamp = temp_list[1].(string)

			}


			if debug == true {
				fmt.Println()
				fmt.Println("previous_main_thread_timestamp:", previous_main_thread_timestamp, parse_time_to_string(previous_main_thread_timestamp))
				fmt.Println("main_thread_timestamp:", main_thread_timestamp, parse_time_to_string(main_thread_timestamp))
				fmt.Println("previous_progress_report_thread_timestamp:", previous_progress_report_thread_timestamp, parse_time_to_string(previous_progress_report_thread_timestamp))
				fmt.Println("progress_report_thread_timestamp:", progress_report_thread_timestamp, parse_time_to_string(progress_report_thread_timestamp))
				fmt.Println()
			}

			if  main_thread_heartbeat_enabled == true &&  previous_main_thread_timestamp == main_thread_timestamp {

				stopped_threads_counter = stopped_threads_counter + 1

				if main_thread_timestamp == "0" {
					message := "LoudnessCorrection has not started updating main_thread timestamp, the thread has probably crashed and a restart of the script is needed\n"
					error_messages = append(error_messages, message)
				} else {
					time_string := parse_time_to_string(main_thread_timestamp)
					message := fmt.Sprintf("LoudnessCorrection has stopped updating main_thread timestamps. Last update: %s\n", time_string)
					error_messages = append(error_messages, message)
				}
			}

			if progress_report_thread_heartbeat_enabled == true && previous_progress_report_thread_timestamp == progress_report_thread_timestamp {

				stopped_threads_counter = stopped_threads_counter + 1

				if progress_report_thread_timestamp == "0" {
					message := "LoudnessCorrection has not started updating progress_report timestamp, the thread has probably crashed and a restart of the script is needed\n"
					error_messages = append(error_messages, message)
				} else {
					time_string := parse_time_to_string(progress_report_thread_timestamp)
					message := fmt.Sprintf("LoudnessCorrection has stopped updating progress_report timestamps. Last update: %s\n", time_string)
					error_messages = append(error_messages, message)
				}
			}

			if stopped_threads_counter > 0 {

				if alert_email_sent == false {

					if silent_mode == false {

						for _, line := range error_messages {
							fmt.Println(line)
						}
					}

					body := strings.Join(error_messages, "\n")
					send_error_email(message_recipients, message_title, body, message_attachment_path)
					alert_email_sent = true
				}

			} else if alert_email_sent == true {
				// Reset if threads resumed
				alert_email_sent = false
				message := "All Heartbeat timestamps started updating again at: " + current_time_string + "\n"
				send_error_email(message_recipients, message_title, message, message_attachment_path)
			}

			previous_timestamps = loudness_correction_program_info_and_timestamps

		report_lock.RUnlock()
	}
}

// --- Main ---

func main() {

	heartbeat_checker_pid = os.Getpid()
	heartbeat_checker_commandline = strings.Join(os.Args, " ")

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
	gin_instance := gin.New()

	// Add Security Middleware: Max Content Length 100KB
	gin_instance.Use(gin.Recovery(), limit_request_body_size(1024 * 100))

	// Add path to listen to
	gin_instance.POST("/heartbeat", handle_receive_heartbeat)

	port := "9002"

	if p, ok := all_settings_dict["heartbeat_service_port"].(string); ok {
		port = p
	}

	fmt.Printf("Starting HeartBeat Checker on port %s...\n", port)

	if err := gin_instance.Run(":" + port); err != nil {
		log.Fatalf("Server failed: %v", err)
	}

	quit_all_threads_now = true
}


