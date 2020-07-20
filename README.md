# README #
### What is this repository for? ###

* This project reads the sample to pool mappings from Hamilton and pool results for COVID-19 from Panther, analyzes the negative samples and results the negative resulted samples to EPIC.

### What do I need to run this? ###
* python 3 or above installed.
* The input arguments needed are as follows:
	* -s <sample to pool mapping file> - path to an excel file(.xlsx) that contains the sample to pool mapping information.
	* -p <pool results file> - path to the results file which contains the result information of all the pools that are tested.
	* -o <mirth orders directory> - directory path for the HL7 incoming messages.
	* -r <mirth results directory> - directory path for the resulting HL7 messages.
	* -a <mirth archive directory> - directory path of the archives where ordered messages are moved after resulting it.

### How do I run this? ###

* Download the source code from the repository
* Generate the needed input files (refer the sample files in the repository).
* Note down the source paths for the mirth folders.
* Run the python script as below:
* python3 Pool_Covid19_Panther.py -s <sample_to_pool_mapping_file> -p<pool_results_file> -o<path_to_orders_dir> -r<path_to_results_dir> -a<path_to_archives_dir>
* Give python3 Pool_Covid19_Panther.py -h for help.

### Contribution guidelines ###

* Writing tests
* Code review
* Other guidelines

### Who do I talk to? ###

* Repo owner or admin
* Other community or team contact