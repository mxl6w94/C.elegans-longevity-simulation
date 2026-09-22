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

---

### AI User Story

#### User Story: As a User, I want to search for genes by name or identifier so I can quickly find the genes I want to include in a prediction.

> *Gene Search - Success*
> - **Given**: the user is on the webpage
> - **When**: the user enters a full or partial gene name or identifier in the search field
> - **Then**: a list of matching genes is displayed and each can be added to the selection

> *Gene Search - Success (Add to Selection)*
> - **Given**: search results are displayed
> - **When**: the user selects a gene from the results
> - **Then**: the gene is added to the current selection and marked as selected in the results list

> *Gene Search - Failure (No Matches)*
> - **Given**: the user is on the webpage
> - **When**: the user enters a search term that matches no genes in the dataset
> - **Then**: a message is displayed indicating no matching genes were found

> *Gene Search - Failure (Duplicate Selection)*
> - **Given**: a gene is already in the current selection
> - **When**: the user tries to add the same gene again from the search results
> - **Then**: the gene is not added a second time and the user is told it is already selected

> *Gene Search - Failure (Search Service Error)*
> - **Given**: the user is on the webpage
> - **When**: the user enters a search term and the gene lookup fails or times out
> - **Then**: an error message is displayed, the search term is preserved, and the user is given the option to retry

---

1. Similarities - Both describe behavior from the user's point of view and both pair each success path with at least one failure path that ends in a message to the user. They also address the same feature area.
2. Differences - My stories cover the full workflow at a high level, from reaching the site to selecting genes and viewing results, with one success and one failure scenario each. The AI story is narrower as it covers a single interaction with five scenarios. The AI suggestions offer more of the explanation for user motivation.
3. Revisions - We will possibly include the criteria that the AI suggested as it is useful.
