# 0003_[R]_penicillin_CUBIST.R

# Load the plumber library
library(plumber)
library(Cubist)

# Load the Random Forest model
CubistModel <- readRDS("../Models/0003_[R]_penicillin_CUBIST.rds")

# Define a prediction function
#* @post /0003_penicillin_CUBIST
#* @param req The request containing the input JSON data
#* @response 200 Returns the predictions
function(req) {
  
  # Convert the JSON input to a data frame
  new_data <- as.data.frame(jsonlite::fromJSON(req$postBody, flatten = TRUE))
  
  # Make the prediction
  predictions <- predict(CubistModel, new_data)
  
  # Return the predictions as a list
  return(list(predictions = predictions))
}
