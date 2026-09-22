# 3 critical features:

# Users will see a predicted life expectancy of the worm for a given set of genetic parameters. 

-
-
-

# Users will have a visual of what the worm will look like for the given biological age in relation to chronological time. 

-
-
-


# Users will be presented with a Web-Accessible User Interface for controlling gene selection and retrieve predictions [[Tyler Bullard]]


## Acceptance Criteria:
  
  #### User Story: As a User, I want to access the app's web page.
  
> *Access - Success*
> - **Given**: the user has a browser open
> - **When**: the user enters the web address
> - **Then**: the website page is displayed

> *Access - Failure*
> - **Given**: the user has a browser open
> - **When**: the user enters the web address and the server is down or unreachable
> - **Then**: an error message is displayed indicating the service is temporarily unavailable
  
#### User Story: As a User, I want to select genes for C. Elegans life expectancy predictions.
    
> *Gene Selection - Success*
> - **Given**: the user is on the webpage
> - **When**: the user selects a set of genes
> - **Then**: a prediction is made

> *Gene Selection - Failure (No Genes Selected)*
> - **Given**: the user is on the webpage
> - **When**: the user submits a request without selecting any genes
> - **Then**: no prediction is made and the user is prompted to select at least one gene

  
#### User Story: As a User, I want to view C. Elegans life expectancy predictions.
   
> *Data Representation - Success*
> - **Given**: a prediction has been made
> - **When**: the user requests to view the prediction
> - **Then**: the prediction data is represented on the user interface

> *Data Representation - Failure*
> - **Given**: no prediction has been made
> - **When**: the user requests to view the prediction
> - **Then**: a message is displayed indicating no prediction exists and prompting the user to select genes
