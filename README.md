# Geochem Classifier script
### Automated geochem data classification assistant.
### Demo version for GitHub
### Developed by: Jakub Pitera 

Geochem Classifier will move duplicated filenames aside and perform preliminary classification of geochem files. 
Finally it will produce a report to be used when filling the tracking sheet.

User has to review this classification looking for any outliers and mistakes. PDFs are stored apart for further review.

In order to run this tool prepare the folder structure with appropriate names as following: 
<well> /
    <datapack_1> /
    <datapack_2> / 
    <datapack_3> /
    etc...

Classification is dependant on 'classification_dictionary.csv' which should be curated by the users (not available on GitHub).
