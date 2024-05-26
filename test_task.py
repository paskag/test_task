import pandas as pd
import numpy as np
from copy import deepcopy
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

class AssuredAllies:
    def __init__(self, applicants=None, sessions=None, events=None):
        """
        Initializing 

        Args:
            applicants (DataFrame): personal details of the applicants that scheduled an underwriting sessions
            sessions (DataFrame): administrative details about the session and its status
            events (DataFrame): events related to the underwriting session
        """
        self.applicants = deepcopy(applicants)
        self.sessions = deepcopy(sessions)
        self.events = deepcopy(events)
        self._applicants_orig = deepcopy(applicants) #save the origin file just in case
        self._sessions_orig = deepcopy(sessions) #save the origin file just in case
        self._events_orig = deepcopy(events) #save the origin file just in case

    def formatting_dates(self):
        """ 
        Here we need to format all the dates to dateformate type
        """
        self.applicants["birth_date"] = pd.to_datetime(self.applicants["birth_date"])
        self.sessions["risk_class_decision_datetime"] = pd.to_datetime(self.sessions["risk_class_decision_datetime"], format='mixed').dt.tz_localize(None)
        self.events["event_datetime"] = pd.to_datetime(self.events["event_datetime"], format='mixed').dt.tz_localize(None)
        self.events = self.events.sort_values("event_datetime").reset_index(drop=True) #sort in chronological order

    def delete_unrelevant_info(self):
        '''
        Here we delete unrelevant information. 
        For example, we need only applicants whoes session was completed.
        '''
        #in my opinion we need to check only such "session_id" whoes status is completed
        self.sessions = self.sessions[self.sessions['session_status'] == 'completed'].reset_index(drop=True) 
        self.events = self.events[self.events["session_id"].isin(self.sessions["session_id"])] #leave only relevant sessions
        self.events = self.events.drop_duplicates() #delete duplicated rows
        #we need to know the time when the applicant completes the test and when ally submits the form.
        #so event_type "end_of_underwriting" and "Ally submitted test results" are MUST have
        self.events = self.events[self.events["event_type"].isin(["end_of_underwriting", "Ally submitted test results"])]
        #we also need to have 2 events for EACH session "end_of_underwriting" and "Ally submitted test results"
        #there are some sessions that have only 1 of needed events. so we need to get the list of session_id with 2 events
        session_id_gr = self.events.groupby('session_id')['event_type'].nunique() #we groupby session_id and check number of unique events
        session_id_relevant = list(session_id_gr[session_id_gr == 2].index) #here we get the list of session_id that have BOTH "end_of_underwriting" and "Ally submitted test results"
        self.events = self.events[self.events["session_id"].isin(session_id_relevant)] #here we leave only relevant rows
        #there are some session_id that has several rows of "end_of_underwriting". so there is the question. 
        #which time of "end_of_underwriting": the first time or the last time?
        #I decided to choose the last time because it ensures that this is the final event of the test 
        #and takes into account the possibility that previous termination events were erroneous
        self.events = self.events.drop_duplicates(subset=["session_id", "event_type"], keep='last')
        self.events = self.events.reset_index(drop=True)

    def time_counting(self):
        '''
        Here we will calculate the time spent between "end_of_underwriting" and "Ally submitted test results" for each session_id
        '''
        #we will devide datasets into two: one for the "end_of_underwriting", the other for the end "Ally submitted test results"
        df_end = self.events[self.events["event_type"] == "end_of_underwriting"].set_index('session_id')
        df_ally = self.events[self.events["event_type"] == "Ally submitted test results"].set_index('session_id')
        #now we need to merge these datasets
        self.events = df_end.join(df_ally, lsuffix='_end', rsuffix='_ally').reset_index()
        self.events = self.events.drop("applicant_id_ally", axis=1).rename({"applicant_id_end": "applicant_id"}, axis=1) #drop duplicated column
        #now we need to calculate the time and convert them to seconds
        self.events["time_diff"] = (self.events["event_datetime_ally"] - self.events["event_datetime_end"]).dt.total_seconds()
        #delete rows where time_diff is below zero
        self.events = self.events[self.events["time_diff"] > 0].reset_index(drop=True)
            
    def devide_df(self, date="15-03-2259"):
        '''
        Here we devide the dataframe into 2: before 15.03.2259 and after. 
        This is the date when a certain change has been made.
        '''
        date = pd.Timestamp(date)
        self.df_before = self.events[self.events["event_datetime_end"] < date].reset_index(drop=True)
        self.df_after = self.events[self.events["event_datetime_end"] >= date].reset_index(drop=True)
        
    def remove_outlires(self):
        '''
        Here we remove oulires from the data
        '''
        #we will now remove outliers from our dataset using the interquartile range method (IQR)
        #calculation of the first (Q1) and third (Q3) quartiles
        q1_before, q3_before = self.df_before["time_diff"].quantile(0.25), self.df_before["time_diff"].quantile(0.75)
        q1_after, q3_after = self.df_after["time_diff"].quantile(0.25), self.df_after["time_diff"].quantile(0.75)
        iqr_before = q3_before - q1_before
        iqr_after = q3_after - q1_after
        #we need to find the upper and lower bounds of the range
        lower_bound_before, upper_bound_before = q1_before - 1.5 * iqr_before, q3_before + 1.5 * iqr_before
        lower_bound_after, upper_bound_after = q1_after - 1.5 * iqr_after, q3_after + 1.5 * iqr_after
        #delete outlires
        self.df_before = self.df_before[(self.df_before["time_diff"] >= lower_bound_before) & (self.df_before["time_diff"] <= upper_bound_before)]
        self.df_after = self.df_after[(self.df_after["time_diff"] >= lower_bound_after) & (self.df_after["time_diff"] <= upper_bound_after)]
        self.df_before, self.df_after = self.df_before.reset_index(drop=True), self.df_after.reset_index(drop=True)
        
    def build_graph(self):
        '''
        Here we will plot the distribution and boxplot of time_diff
        '''
        print("These are graphs of the distribution of the values of the time spent on to ﬁll in the test results form")
        fig, ax = plt.subplots(2, 2, figsize=(15, 7))
        ax[0, 0].set_title("Before 15/03/2259") 
        ax[0, 1].set_title("After 15/03/2259") 
        #histplot
        sns.histplot(data=self.df_before, x="time_diff", kde=True, ax=ax[0, 0], bins=100)
        sns.histplot(data=self.df_after, x="time_diff", kde=True, ax=ax[0, 1], bins=100)
        ax[0, 1].set_xticks(range(0, 2800, 100))
        ax[0, 1].set_xticklabels(ax[0, 1].get_xticklabels(), rotation=45)
        ax[0, 1].set_yticks(list(range(0, 11)))
        #boxplot
        sns.boxplot(data=self.df_before, x="time_diff", ax=ax[1, 0])
        sns.boxplot(data=self.df_after, x="time_diff", ax=ax[1, 1])
        ax[1, 1].set_xticks(range(0, 2800, 100))
        ax[1, 1].set_xticklabels(ax[0, 1].get_xticklabels(), rotation=45)
        plt.show()
    
    def result_statistical_methods(self):
        '''
        Here we get results using statistical methods
        '''
        #now we need to check the normality of the distribution. We will use Shapiro Wilk test
        #Hypothesis 1 - distribution is normal. Hypothesis 2 - distribution is unnormal
        #if pValue < 0.05 - that means that we can reject Hypothesis 1. In that case the distribution will be unnormal
        stat_before, p_before = stats.shapiro(self.df_before['time_diff'])
        stat_after, p_after = stats.shapiro(self.df_after['time_diff'])
        if p_before > 0.05 and p_after > 0.05: #which means that distribution is normal
            t_stat, p_value = stats.ttest_ind(self.df_before['time_diff'], self.df_after['time_diff']) #Student's t-test
        else: #which means that distribution is unnormal
            u_stat, p_value = stats.mannwhitneyu(self.df_before['time_diff'], self.df_after['time_diff'])
        #calculate the average values of the "time_diff" column before and after the date
        self.mean_before, self.mean_after = self.df_before["time_diff"].mean().round(3), self.df_after["time_diff"].mean().round(3)
        #interpretation of the result
        #Hypothesis 1 - There is NO significant difference in the average time between the 'end' and 'ally' events before and after the process change.
        #Hypothesis 2 - There is a significant difference in the average time between the 'end' and 'ally' events.
        #if pValue < 0.05 - that means that we can reject Hypothesis 1
        if p_value < 0.05:
            print("The changes are statistically significant.", end="\n\n")
            print(f"The mean value of the time spent before 15/03/2259: {self.mean_before} seconds. After: {self.mean_after} seconds.", end='\n\n')
            print("The average value of the time spent on processing to fill in the test results form before the date 15/03/2259")
            if self.mean_before > self.mean_after:
                print("is BIGGER than the same value after the date 15/03/2259", end="\n\n")
                print("FINAL RESULT: The goal has been achived:")
                print("the change in the underwriting ﬂow on the ally side ACHIEVED the purpose of shortening the time to ﬁll in the test results form")
            else:
                print("is LOWER than the same value after the date 15/03/2259", end="\n\n")
                print("FINAL RESULT: Unfortunately, the goal hasn't been achived:")
                print("the change in the underwriting ﬂow on the ally side HASN'T ACHIEVED the purpose of shortening the time to ﬁll in the test results form.")
                print("The time to fill in the test results form has become even longer on average.")
            print()
        else:
            print("The changes are not statistically significant. The average time did not change after the process change.")
                    
    def start(self):
        '''
        Launching the program
        '''
        self.formatting_dates()
        self.delete_unrelevant_info()
        self.time_counting()
        self.devide_df()
        self.remove_outlires()
        self.build_graph()
        self.result_statistical_methods()
