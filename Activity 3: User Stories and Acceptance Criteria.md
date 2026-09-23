# 3 critical features:

# Users will see a predicted life expectancy of the worm for a given set of genetic parameters. 

-
-
-

# Users will have a visual of what the worm will look like for the given biological age in relation to chronological time [[Caleb Walton]]. 
**My story and acceptance criteria:** 

User story: As a user in the field of Biology, I want to see an image of what a worm with a specific age and set of genes would potentially look like so that I have a visual of the worm for the given biological age in relation to chronological time. 

Acceptance criteria: 

Given: The user has already selected the desired genes and generated the predicted lifespan 

And: is on the prediction graph with the option to see a visual of the worm. 

 Scenario 1: The user generates the image with no errors. 

When: The user selects an age in the range of the predicted lifespan graph’s duration 

And: The user confirms their selection. 

Then: An image of the potential appearance of the worm is displayed. 

 Scenario 2: The age entered by the user is out of range of the lifespan graph’s duration. 

When: The user selects an age not in the range of the lifespan graph’s duration 

And: The user confirms their selection. 

Then: An error is displayed signaling the age is out of range.


**AI-generated story and acceptance criteria using ChatGPT:** 

User story: As a user, I want to view a visual representation of the C. elegans worm at a specified biological age so that I can see what the worm is predicted to look like in relation to its chronological time and selected gene expression. 

Acceptance criteria: 

  Scenario 1: The visual display is successful with no errors. 

Given: the user has selected the desired genes and specified a biological age and the system has generated a predicted lifespan graph 

When: the user selects the option to view the worm at the specified biological age 

Then: the system displays a visual representation of the C. elegans worm corresponding to the selected biological age and the predicted lifespan information 

Given: the user is viewing the visual representation 

When: the user changes the specified biological age 

Then: the system updates the visual representation to reflect the worm's predicted appearance at the newly selected biological age 

(Note from Caleb: the next scenario was prompted and generated after the above scenario was generated) 

  Scenario 2: The visual display fails due to the specified age being out of range. 

Given: the user has selected a set of genes and the system has generated a predicted lifespan graph with a defined biological age range 

When: the user specifies a biological age that falls outside the range of the predicted lifespan graph and attempts to generate a visual representation 

Then: the system displays an error message informing the user that the specified biological age is outside the predicted lifespan range and prompts the user to enter a biological age within the valid range


**Comparison:** 

The user stories of the non-AI and AI versions are mostly the same. Both stories describe the same goal in a very similar way. However, the acceptance criteria are where the versions differ. For the non-AI version, it starts with a given statement that applies to both the success and failure scenarios, and then it starts specifying details for each unique scenario. The AI version had only one scenario that has two parts: one initializes the image and the other updates it. I then prompted the AI to add a second scenario where the program fails to display a visual due to an error. I believe the weakest aspect of the AI version is that it initially had only one scenario, which is why I generated a second scenario. I also added markers for scenarios 1 and 2 myself for more clarity. Overall, I think the AI version after my revisions is better because the acceptance criteria are described more clearly, making it easier to understand and follow for a software engineering team. 





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

Users will be presented with a select few genes to turn on and off, with predicted growth rate responding accordingly. [[Michael LeBlanc]]
Acceptance Criteria:
User Story: As a User, I want the model to accurately predict a C. elegans growth rate based on chosen genes.
Genes chosen for the model - Success

Given: the user is on the webpage

When: the user enters a gene or multiple genes to simulate

Then: the worm's predicted growth rate and life expectancy is displayed

Genes chosen for the model - Failure (Invalid Gene Identifier)

Given: the user is on the webpage

When: the user enters a gene identifier that does not map to the underlying metabolic reconstruction

Then: no prediction is generated and an error message prompts the user to verify the gene name

Genes chosen for the model - Failure (Model Infeasibility)

Given: the user is on the webpage

When: the user selects a combination of genes that results in an unsolvable or biologically non-viable metabolic state

Then: a message is displayed indicating the simulation failed to find a valid solution for the specified parameters

User Story: As a User, I want to toggle specific genes on and off so I can quickly compare changes to the predicted growth rate.
Toggle Gene State - Success

Given: the user has a baseline prediction loaded on the webpage

When: the user toggles a selected gene from "on" to "off"

Then: the model recalculates the metabolic routing and dynamically displays the updated growth rate

Toggle Gene State - Failure (No Metabolic Impact)

Given: the user has a baseline prediction loaded on the webpage

When: the user toggles a gene that does not constrain any active reactions under the current simulated conditions

Then: the displayed growth rate remains unchanged and a tooltip indicates the gene knockout has no impact on the objective function

AI User Story
User Story: As a User, I want to apply transcriptomic differential expression datasets to constrain reaction flux bounds, so the growth rate prediction reflects realistic metabolic rerouting rather than just binary knockouts.
Transcriptomic Constraint - Success

Given: the user is on the webpage

When: the user applies a valid transcriptomic expression dataset

Then: the system scales the model's reaction flux bounds accordingly and generates an updated growth rate prediction

Transcriptomic Constraint - Failure (Invalid Format)

Given: the user is on the webpage

When: the user attempts to apply a dataset with improperly formatted expression fold changes

Then: the system rejects the input and displays an error message detailing the required format

Transcriptomic Constraint - Failure (Zero Biomass Production)

Given: a transcriptomic dataset is successfully applied

When: the constrained flux bounds strictly prevent the objective function from producing any biomass

Then: the prediction returns a zero growth rate and flags the specific constrained reactions causing the halt

Similarities - Both sets of stories utilize the standard BDD (Given/When/Then) format to outline clear success and failure pathways, maintaining a focus on user interaction with the C. elegans simulation interface and providing feedback when errors occur.

Differences - The original stories focus on the high-level frontend interaction of simply inputting or toggling genes on and off to view a growth rate. The AI story introduces a deeper computational biology workflow, shifting the focus toward using transcriptomic data to constrain actual reaction flux bounds to simulate metabolic rerouting.

Revisions - We will integrate the AI's criteria, as adjusting reaction flux bounds based on expression datasets provides a much more robust and biologically accurate simulation methodology for predicting growth rates than simple binary gene knockouts.
