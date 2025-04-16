# 0002_[R]_penicillin_RF.R

# Load the plumber library
library(plumber)
library(ranger)

# Load the Random Forest model
RFmodel <- readRDS("../Models/0002_[R]_penicillin_RF.rds")

# Define a prediction function
#* @post /0002_penicillin_RF
#* @param req The request containing the input JSON data
#* @response 200 Returns the predictions
function(req) {

  # Convert the JSON input to a data frame
  new_data <- as.data.frame(jsonlite::fromJSON(req$postBody, flatten = TRUE))
  
  # Make the prediction
  predictions <- predict(RFmodel, new_data)$predictions
  
  # Return the predictions as a list
  return(list(predictions = predictions))
}
