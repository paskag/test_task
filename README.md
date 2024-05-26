# I completed this task as a test assignment for one of the companies

## Background
#### We made a certain change in our underwriting application that should simplify the process of ﬁlling in and submitting the underwriting test results form by the ally. This simpliﬁcation should result in a shortening of the time it takes from the moment an applicant completes the underwriting tests and until the ally submits the form reporting on the test results. This change was applied on March 15, 2259 and we would like to test whether the change has achieved its purpose.

## Data
#### The data you will be using to answer the questions in this exercise is attached to the email message you got:

1. Applicants table - personal details of the applicants that scheduled an underwriting sessions

2. Sessions table - administrative details about the session and its status

3. Events table - events related to the underwriting session

4. Data dictionary - list of ﬁelds in each table and their description

| Table         |       Field        | Description                          |
| ------------- |:------------------:| -----                                |
| Applicant     | applicant_id       | Unique identiﬁer of the applicant    |
|               | session_id         | Unique identiﬁer of the session                                 |
|               | ﬁrst_name          | Applicant’s ﬁrst name                              |
|               | last_name          | Applicant’s last name                                  |
|               | agent_name         | Name of agent who referred the applicant                                 |
|               | ally_name          | Name of ally who conducted the session                                   |
|               | birth_date         | Applicant’s gender: F, M, Other                                  |
|               | gender             | Applicant’s date of birth                                    |
| Session       | session_id         | Unique identiﬁer of the session                                    |
|               | applicant_id       | Unique identiﬁer of the applicant                                  |
|               | session_status     | Status of the session                                  |
|               | risk_class_decision_datetime | Timestamp of when the notiﬁcation about the applicant’s risk class was sent to the agent |
| Events        | session_id         | Unique identiﬁer of the session    |
|               | applicant_id       | Unique identiﬁer of the applicant                               |
|               | event_type         | Type of event                            |
|               | event_user         | What side triggered the event                                 |
|               | event_datetime     | Timestamp of the event                                |

## Goal
#### We would like to get an answer to the following question: Has the change in the underwriting ﬂow on the ally side achieved the purpose of shortening the time to ﬁll in the test results form?

## Results
#### The results of my analysis can be viewed in this [presenetation file](presentation.ipynb)
