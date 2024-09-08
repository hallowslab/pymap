#!/bin/bash

# Configuration
sender="pymap@pymap.lan"  # Replace with your email address
recipients=("pymap@pymap.lan" "test@pymap.lan")  # Replace with your recipient email addresses
num_messages=50  # Number of messages to send to each recipient

# Generate random subjects and bodies
generate_random_subject() {
  subjects=("Subject A" "Subject B" "Subject C")
  echo "${subjects[$RANDOM % ${#subjects[@]}]}"
}

generate_random_body() {
  bodies=("Message body A" "Message body B" "Message body C")
  echo "${bodies[$RANDOM % ${#bodies[@]}]}"
}

# Loop through recipients and send multiple emails
for recipient in "${recipients[@]}"; do
  for ((i = 1; i <= num_messages; i++)); do
    subject=$(generate_random_subject)
    body=$(generate_random_body)

    # Send the email
    echo "Generating message from $sender to $recipient" >> generate.txt
    echo "$body" | mail -s "$subject" -r "$sender" "$recipient"
    
    echo "Sent email #$i to $recipient with subject '$subject'"
  done
done
