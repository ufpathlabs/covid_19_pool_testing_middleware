# README #

### Project Overview ###
* This repository provides a script for the deconvolution of pooled COVID-19 samples run on a Hologic Panther system from samples prepared on a Hamilton NGS Star system. This script also provides the tools to result all negative pooled samples directly into EPIC EMR system. Any pools that are positive are not resulted.
* This project reads the sample to pool mapping file from Hamilton and pool results file from Panther System, analyzes the negative samples and results the negative resulted samples to EPIC

### Will this benefit if I am not using Hamilton and Panther System? ###
* The approach presented here is an example based on Hamilton and Panther systems. However, similar methodology can be easily adopted for integrating other systems by modifying this python code or writing new code.

### What is the benefit of this approach? ###
* With the rise in COVID-19 cases, the usage of test resources is increasing constantly. Due to this increase and sudden demand for testing, there is a worldwide shortage of testing resources and delays in almost every aspect of supply chains for COVID reagents. Here at the University of Florida, there was a demand for return to work COVID-19 screening in a large asymptomatic population. To accommodate this demand and conserve testing materials, samples were pooled in order to achieve both goals.
* Sample pooling allows multiple samples to be tested using fewer testing resources by pooling multiple samples together to be tested at one time. Samples from multiple individuals are tested in a pool using one test, rather than running each individual sample on its own test. If the pool is positive, it means that one or more of the individuals tested in that pool may be infected, so each of the samples in that pool are tested again individually. If a Pool sample is Negative, then all individual samples are resulted as negative and no repeat testing is required. Because the samples are pooled, fewer testing supplies are used and more tests can be run at the same time. This testing strategy is most efficient in areas with low prevalence, meaning most results are expected to be negative.
* Pooling on the Hamilton NGS Star system is able to accommodate a pool size of 2 to 10 samples. This allows for flexibility as the percent positivity increases or decreases in in the sample population. As the percent positivity increases in a population the pool size should be reduced to reduce the number of repeat testing that is required due to positive pools.
* Individual samples are barcoded and placed onto the deck of the Hamilton NGS Star. A unique barcoded label also needs to be generated for each pool sample. For example, if you are pooling 1 to 5 and are testing 100 individuals, you would need 20 uniquely labeled pool tubes. To run the pool samples on the Hologic Panther system, the labeled Pool tubes are Hologic Specimen Lysis tubes. The 20 pool lysis tubes are placed onto the deck of the Hamilton NGS Star. The transfer program is run and equal amounts of sample is transferred from the primary sample tube to the target pool lysis tube. In the case of the Hologic Panther system a total sample volume of 500uL is added to the pool lysis tubes. For a 1 to 5 pool, 100uL of each sample is added to the target lysis pool tube.
* When the transfer program is complete, an excel file is generated that contains the original sample, the pool it was transferred to and the volume that was transferred to the target lysis pool tube.
* The pool lysis tubes are transferred to the Hologic Panther system and run per the manufactures instructions. When completed, the results are exported from the panther system as a .LIS file.

### Overall Workflow ###
![workflow image](COVID_19_Pooling_WorkFlow_V1.png)

### How are the results interpreted and reported? ###
* At UF Health, clinical laboratory testing results are interfaced with EPIC Beaker to the NextGen Connect Integration Engine (Formerly MirthConnect), which pushes the results into Beaker.

* Step A. As shown in the above figure, as soon as COVID-19 test is ordered and a specimen is collected below two events happen, 
	
	* (A.1.) Test order shows up on the pathology lab worklist in Epic Beaker LIS.
	
	* (A.2.) We configured our electronic interface software EPIC Bridges and NextGen Connect for simultaneously sending an order HL7 message to a network folder.  This HL7 file contains information related to the patient, test order, specimen ID, and empty test result line. See example outgoing HL7 files in "Input_Files/Incoming_HL7" folder.

* Step B. Our middleware script ("COVID19_Pool_Testing_Panther.py") will automatically do the following, 
	
	* (B.1.) After reading the pool results file from the Hologic Panther System (e.g., "Panther_POOL_RESULTS.lis.xls") we categorize the pool result as "Negative" if below criteria is met else as "Positive". It is to be noted that Panther output file contain only Pool ID not the original Sample IDs.
		* column "Interpretation 1" is less than 325 (its relative light unit - RLU Score) AND 
		* column "Interpretation 2" is "valid" AND 
		* column "Interpretation 3" is " Negative" 
	
	* (B.2.) The samples associated with "Negative" pools are also categorized as "Negative". Sample IDs are retrieved by linking "Specimen Barcode" column (which is a pool sample ID) in "Panther_POOL_RESULTS.lis" with "Pooled Sample Barcode" column in "Hamilton_SAMPLE_POOL_MAP.xlsx" file.
	
	* (B.3.) All "Negative� sample results are reported back to EPIC Beaker. This is done by detecting corresponding incoming HL7 order message file based on the sample ID, and inserting a result value (as "Not Detected" to OBX record) into the HL7 message generating outgoing HL7 message. Outgoing HL7 message will be appended with test protocol description to NTE record that appears in the comment box in EPIC Beaker. This outgoing HL7 message is placed on the network drive. See example outgoing HL7 files in "Output_Files/Result_HL7" folder.
	
	* (B.4.) Samples corresponding to "Positive" pools (from B.1) will not be generating any outgoing HL7 files. Thus, results for these samples are reported to EPIC Beaker but will be re-tested individually because at least one sample in that pool is positive.

* Step C. Outgoing HL7 messages generated above (B.3) are automatically picked up by NextGen Connect and pushed into Epic Beaker.
		
### What do I need to run this? ###
* python 3 or above installed.
* The input arguments needed are as follows:
	* -s <sample to pool mapping file> - path to an excel file(.xlsx) that contains the sample to pool mapping information.
	* -p <pool results file> - path to the results file which contains the result information of all the pools that are tested.
	* -o <mirth orders directory> - directory path for the HL7 incoming messages.
	* -r <mirth results directory> - directory path for the resulting HL7 messages.
	* -a <mirth archive directory> - directory path of the archives where ordered messages are moved after resulting it.

### What do the input files mean? ###
* Hamilton_SAMPLE_POOL_MAP.xlsx
	* Gives us the mapping of each sample to a pool. Using this file, we interpret the results of each sample based on the pool result to which the sample is associated with.
		* Pooled Sample Barcode - The barcode ID of the pools.
		* Source Sample Barcode - The barcode ID of each samples.
* Panther_POOL_RESULTS.lis.xls
	* Gives the results of the pools that are tested for.
	* The columns from this file that we use are:
		* Specimen Barcode - The pool barcode ID. It is the same ID that is used in the Pool_Map file to map samples to a pool.
		* Interpretation1 - It contains the RLU Score. If the score is less than 350 and the result is valid, then the pool is categorized as "Negative".
		* Interpretation2 - If the value is "valid", it means the test has been conducted succesfully for this pool. Otherwise, it reports "Invalid".
		* Interpretation3 - This columns gives the actual result of the test for this pool. It gives either "Positive" or "Negative" if the pool is tested positve or negative correspondingly.

### What is the output? ###
* After interpreting all the pool results, an output excel file, TST_FINAL.xlsx is generated with detailed information for all the samples.
* It starts with the sample ID, pool ID to which this sample is associated, result for the sample, and says if the sample results are uploaded to EPIC or not.
* If the pool is tested Negative, then all the associated samples' results are uploaded to EPIC. Otherwise, they are not uploaded at this time.
* hl7-pooled-COVID_19-100004162-output.txt - In the output HL7 message, the result is added in the OBX segment.

		MSH|^~\&|IM|87380||1230600115|20200707131123||ORU^R01|6.373058828372929e+17|P|2.4|||||||||||
		PID|1||32^^^^||1^SAMPLE^^|||||||||||||||||
		PV1|||||||||||||||||||
		ORC|RE|PLMO20-001480|PLMO20-001480||||^^^^^R^^||||||||||||||||
		OBR|1|PLMO20-001480|100004162^|12350000^SARS-CoV-2, NAA UFHPL MOLECULAR|||20200626100800||||Lab Collect||||Universal Tr&Universal Transport Media (UTM)^^^NasoPharynx&NasoPharynx|||||||20200707131123|||P||^^^^^R^^||
		NTE|1|L|This test was developed and its performance characteristics determined by the University of Florida Health Pathology Laboratories (UF Health PathLabs) Laboratories. The assay was validated to allow for pooled sample testing.
		NTE|2|L|This test has not been FDA cleared or approved. This test has been authorized by FDA under an Emergency Use Authorization (EUA).
		NTE|3|L|This test has been validated in accordance with the FDA's Guidance Document "Policy for Diagnostics Testing in Laboratories Certified to Perform High Complexity Testing under to Emergency Use Authorization for Coronavirus Disease-2019 during the Public Health Emergency" issued on February 29th, 2020. FDA independent review of this validation is pending.
		NTE|4|L|This test is only authorized for the duration of time the declaration that circumstances exist justifying the authorization of the emergency use of in vitro diagnostic tests for detection of SARS-CoV-2 virus and/or diagnosis of COVID-19 infection under section 564(b)(1) of the Act, 21U.S.C. 360bbb-3(b)(1), unless the authorization is terminated or revoked sooner.
		NTE|5|L|The results of this test are not intended to be used as the sole means for clinical diagnosis and/ or patient management decisions.
		NTE|6|L|UFHealth PathLabs is authorized under Clinical Laboratory Improvement Amendments (CLIA) to perform high-complexity testing. Testing performed at UF Health PathLabs 4800 SW 35th Drive, Gainesville, FL 32608.
		NTE|7|L|
		OBX|1|ST|12350000^SARS-COV-2, NAA|12350000|Not Detected||-||||P|||20200707131123|||123648|UFHPL Panther2|20200707131123

### How do I run this? ###

* Download the source code from the repository
* Generate the needed input files (refer the sample files in the repository).
* Note down the source paths for the mirth folders.
* Run the python script as below:

		python3 COVID19_Pool_Testing_Panther.py -s Hamilton_SAMPLE_POOL_MAP.xlsx -p Panther_POOL_RESULTS.lis.xls -o /Input_Files/Incoming_HL7/ -r /Output_Files/Result_HL7/ -a /Input_Files/Orders_Archive/

### Who do I talk to? ###

* Dr. Srikar Chamala
* Director Biomedical Informatics
* Department of Pathology, Immunology and Laboratory Medicine, University of Florida
* schamala@ufl.edu | [chamalalab.org](https://chamalalab.org/)


[![Logo](Logo.png)](http://chamalalab.org/)