# main.R

# Load the plumber library
library(plumber)

# Set working directory
#setwd("/R")


# Crea una nueva API con `pr()`
combined_api <- pr()

# Carga y añade los endpoints de la primera API
r1 <- plumb("0002_[R]_penicillin_RF__REST__.R")
combined_api$mount("/rf", r1)  # Monta la API RF en la ruta /rf

# Carga y añade los endpoints de la segunda API
r2 <- plumb("0003_[R]_penicillin_CUBIST__REST__.R")
combined_api$mount("/cubist", r2)  # Monta la API Cubist en la ruta /cubist

# Inicia la API combinada en el puerto 8000
combined_api$run(port = 8000)

