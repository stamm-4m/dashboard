# Load necessary library for making HTTP requests
library(httr)
library(jsonlite)  # To work with JSON

# Example data that matches your model's expected input format
example_data <- data.frame(
  temperature = 298.22, 
  pH = 6.4472,
  dissolved_oxygen_concentration = 30,
  agitator = 100,
  CO2_percent_in_off_gas = 0.089514,
  oxygen_in_percent_in_off_gas = 0.19595,
  vessel_volume = 58479,
  sugar_feed_rate = 8
  # Add more features as per your model's input requirements
)



# Convert the example data to JSON
example_json <- toJSON(example_data)


######################################### Random Forest ######################################### 

# Make a POST request to the API
response <- POST(
  url = "http://localhost:8000/0002_penicillin_RF",  # API endpoint
  body = example_json,                     # Send the JSON data
  encode = "json"                          # Specify that the body is JSON
)

# Check the response
print(content(response))
#################################################################################################

############################################ CUBIST ############################################# 
# Make a POST request to the API
response <- POST(
  url = "http://localhost:8000/0003_penicillin_CUBIST",  # API endpoint
  body = example_json,                     # Send the JSON data
  encode = "json"                          # Specify that the body is JSON
)

# Check the response
print(content(response))
#################################################################################################