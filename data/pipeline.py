print('My data pipeline\n---------------------------')
import pandas as pd
from utilsFunctions import handover_over_60, ed_wait_over5hrs

#0
#0 GENERAL PRACTICE

gp=pd.read_csv('raw/GP_Practices/deprivation-at-gp-cluster-level-v3-en-gb.csv')

gpDate = gp[gp['Date'] == '08/04/2026']
# CLUSTER POPULATION
clusterPop = gpDate[gpDate['Data description'].isin(['Cluster population'])]
# print(clusterPop)

#FULLY QUALIFIED GP FTE, 14 CLUSTERS
gp = pd.read_csv('raw/GP_Practices/number-of-gps-employed-in-general-practices-headcount-and-full-time-equivalent-by-gp-type-and-area-v5-en-gb.csv')
gpDate = gp[gp['Date'] == '31/12/2025']
gpFTE = gpDate[gpDate['Data description'] == 'Full-time equivalent (FTE)']
fqGPs = gpFTE[gpFTE['GPType'] == 'Fully qualified GPs']
fqGPs = fqGPs.rename(columns = {'Area_reference':'Cluster_reference'})
# print(fqGPs.columns)
clusterPopSingle = clusterPop.drop_duplicates(subset=['Cluster_reference'])
clusterPopSingle.columns
gpMerge = pd.merge(clusterPopSingle, fqGPs, on='Cluster_reference', how='inner', indicator=True)
gpMerge['Patients per GP FTE'] = gpMerge['Data values_sort_x']/gpMerge['Data values_sort_y']

gpMerge.columns
mergeSelectedCol = gpMerge[['Cluster_reference','Cluster', 'Data description_x', 'Data values_x', 'Data description_y', 'Data values_y', 'Patients per GP FTE']]
print(mergeSelectedCol)

#1
#1 ROUTE
# PERIOD JAN 2026 - JUNE 2026
#ROUTE:> A SHARE OF MAJOR ED ATTENDANCE ARRIVING BY AMBULANCE.

asi19ii=pd.read_excel('raw/WAST/Dangosyddion Gwasanaethau Ambiwlans 2025 Cyhoeddus Ambulance Services Indicators 2025 Public.xlsx', sheet_name='ASI Data')
asi19ii.columns
# asi19ii['ASI 19ii - Tier 1 Major A&E Units']
lhb = asi19ii[asi19ii['Area'] == 'Betsi Cadwaladr']
lhb = lhb.rename(columns = {'ASI 19ii - Tier 1 Major A&E Units':'999 conveyance'})
timePeriod = lhb.iloc[6:,0:]
# lhb
asi19ii_Tier1 = timePeriod[['999 conveyance']]
asi19ii_Tier1['Date'] = ['January 2026','February 2026', 'March 2026', 'April 2026', 'May 2026', 'June 2026']
#ED
majorED = pd.read_csv('raw/A&E_facilities/emergency-departments-performance-against-waiting-times-targets-october-2009-onwards-v4-en-gb.csv')
majorED = majorED[majorED['Hospital']=='Betsi Cadwaladr']
majorED = majorED[majorED['Hospital Type']=='Major Emergency Departments']
majorED = majorED[majorED['Target']=='Total attendances']
majorED=majorED.iloc[:6,0:][['Date', 'Hospital', 'Data description', 'Data values_sort', 'Hospital Type', 'Target']]
majorED = majorED.rename(columns = {'Hospital':'Area'})
# majorED
# asi19ii_Tier1

# MERGE MAJOR-ED AND ASI TIER 1 DATA
route_ED_ASI = pd.merge(majorED, asi19ii_Tier1, on='Date',how='inner')
route_ED_ASI['Ambulance share %'] = (route_ED_ASI['999 conveyance']/route_ED_ASI['Data values_sort']) * 100
route_ED_ASI['Self-presenting'] = route_ED_ASI['Data values_sort']-route_ED_ASI['999 conveyance']
route_ED_ASI['Self-presenting share %'] = 100 - route_ED_ASI['Ambulance share %']
print(route_ED_ASI)

#2
#2 AMBULANCE:>
#CALLS BY CATEGORY
data = pd.read_csv('raw/WAST/ambulance-activity-and-performance-measures-july-2025-onwards-v11-en-gbFULL.csv')
no_of_calls = data[data['Data description']=='Number of calls']
no_of_calls = no_of_calls.iloc[:30,0:]
print(no_of_calls)
#Here we will add total number of calls for purple + red + Orange + yellow + green for each month.

#MEDIAN AND 90TH PERCENTILE,PURPLE, RED,ORANGE
med_to_90th = data[data['Data description'].isin(['Median ambulance response','90th percentile ambulance response'])]
med_to_90th = med_to_90th[med_to_90th['Date'].str.contains('2026', na=False)]
med_to_90th['Date_parsed'] = pd.to_datetime(med_to_90th['Date'], format="%B %Y") #changing date format
med_to_90th = med_to_90th.sort_values(['Date_parsed', 'Call category_sort'])
med_to_90th = med_to_90th[['Date', 'Data values_sort', 'Data description', 'Call category', 'Local health board']]
print(med_to_90th)
# no_of_calls

#999 conveyance (from route) = purple + red;
#remainder of 999 conveyance = Orange;
#Total number of call - 999 conveyance - remainder of 999 conveyance = yellow + green + some orange


#3
#3 HANDOVER:>
asi_handover=pd.read_excel('raw/WAST/Dangosyddion Gwasanaethau Ambiwlans 2025 Cyhoeddus Ambulance Services Indicators 2025 Public.xlsx', sheet_name='ASI Data')
asi_handover = asi_handover[asi_handover['Area'] == 'Betsi Cadwaladr']
asi_handover = asi_handover[asi_handover['Year'].dt.year == 2026]
asi_handover = asi_handover.rename(columns = {'ASI 20ii - TIER 1 (Major A&E Units) - Notification to handover within 15 minutes ':'Handover within 15 mins','ASI 20ii - TIER 1 (Major A&E Units) - Total Number of Handovers':'Total number of handovers','ASI 21 - Tier 1 Major A&E Units':'Handover lost hours'})
asi_handover['Handover beyond 15 mins'] = asi_handover['Total number of handovers'] - asi_handover['Handover within 15 mins']
asi_handover = asi_handover[['Year','Area','Handover within 15 mins','Total number of handovers','Handover lost hours','Handover beyond 15 mins']]

share_over_60mins = []

for month, row in asi_handover.iterrows():
    lognm, ex, s, mu = handover_over_60(row['Total number of handovers'], row['Handover within 15 mins'], row['Handover lost hours'])
    share_over_60mins.append(lognm)

new_df=pd.DataFrame({'Share_over_60min%':share_over_60mins}, index=asi_handover.index)

asi_handover = pd.concat([asi_handover,new_df],axis=1) 
print(asi_handover)


#4
#4 ED:> # HERE WE WILL MEASURE BY 4HRS = 95% AND THERE SHOULD BE NO  12 HOURS WAIT
data = pd.read_csv('raw/A&E_facilities/emergency-departments-performance-against-waiting-times-targets-october-2009-onwards-v4-en-gb.csv')
majorED = data[data['Hospital Type'] == 'Major Emergency Departments']
major_sites = majorED[majorED['Hospital'].isin(['Wrexham Maelor Hospital (Major)','Ysbyty Glan Clwyd (Major)','Ysbyty Gwynedd (Major)'])]
major_sites = major_sites[major_sites['Date'].str.contains('2026')]
attendance_target = major_sites[major_sites['Data description'].isin(['Total attendances','Percentage of patients who spend less than the target time in an emergency department'])]

total_att = attendance_target[['Date','Hospital','Data description','Data values_sort','Target']]
total_att_ = total_att[total_att['Data description']=='Total attendances']
# total_att_
nhs_target = total_att[total_att['Data description']=='Percentage of patients who spend less than the target time in an emergency department']
# nhs_target
nhs_4h = nhs_target[nhs_target['Target']=='4 hour target']
nhs_4h['Data description']='Percentage of patients'
# nhs_4h.index = total_att_.index
total_att_m1 = pd.merge(total_att_,nhs_4h,on=['Date','Hospital'], how='inner')
nhs_8h = nhs_target[nhs_target['Target']=='8 hour target']
total_att_m1 = pd.merge(total_att_m1,nhs_8h,on=['Date','Hospital'], how='inner')

total_att_m1['Hospital'] = total_att_m1['Hospital'].str[:-8]
total_att_m1['Date_parsed'] = pd.to_datetime(total_att_m1['Date'], format='%B %Y')
total_att_m1 = total_att_m1.sort_values(['Date_parsed','Hospital'])

ed_data = pd.read_csv('raw/A&E_facilities/mean-and-median-time-spent-in-emergency-departments-by-area-hours-and-minutes-april-2012-onwards-v11-en-gb.csv')
ed_data = ed_data[ed_data['Data description_reference'].isin(['Median'])]
ed_data = ed_data[ed_data['Area'].isin(['Ysbyty Glan Clwyd', 'Wrexham Maelor Hospital', 'Ysbyty Gwynedd'])]
ed_data = ed_data[ed_data['Date'].str.contains('2026')]
ed_data = ed_data.rename(columns = {'Area':'Hospital'})
ed_data = ed_data[['Date','Hospital','Data description','Data values_sort']]

ed_data['Date_parsed'] = pd.to_datetime(ed_data['Date'],format='%B %Y')
# ed_data[::-1]
ed_data = ed_data.sort_values(['Date_parsed','Hospital'])
# ed_data

total_att_m2 = pd.merge(total_att_m1,ed_data,on=['Date','Hospital','Date_parsed'],how='inner', suffixes=('','_s'))
total_att_m2[['Share beyond 5hrs','Share within 5hrs']] = total_att_m2.apply(lambda row: ed_wait_over5hrs(row['Data values_sort_y'],row['Data values_sort'],row['Data values_sort_s']), axis=1, result_type='expand')
print(total_att_m2)

#5
#5 ADMISSION:>
data = pd.read_csv('raw/Admissions/outcome-of-attendances-in-major-emergency-departments-april-2012-onwards-v14-en-gb.csv')
data_tp = data[data['Date'].str.contains('2026')]
data_tp['Date_parsed'] = pd.to_datetime(data_tp['Date'],format='%B %Y')
data_tp = data_tp[data_tp['Date_parsed'].dt.month < 7]
same_hosp = data_tp[data_tp['Data description'].isin(['Admitted to the same hospital'])]
diff_hosp = data_tp[data_tp['Data description'] == 'Admitted to a different hospital']
totl_att = data_tp[data_tp['Data description'] == 'Total Attendances']
totl_att = totl_att[['Date_parsed','Date','Data description','Data values_sort']]
# totl_att
same_hosp = same_hosp[['Date_parsed','Date','Data description','Data values_sort']]
# same_hosp
diff_hosp = diff_hosp[['Date_parsed','Date','Data description','Data values_sort']]
# diff_hosp
totl_adm = pd.merge(same_hosp, diff_hosp, on=['Date_parsed','Date'], how='inner')
totl_adm['Total admissions Wales'] = totl_adm['Data values_sort_x'] + totl_adm['Data values_sort_y']

#TOTAL ATTENDANCE WALES (eg.64,882 in January) / TOTAL ADIMISSION WALES = BCUHB SHARE OF ADMISSION in %
totl_att.index = totl_adm.index
totl_adm['Total attendances Wales'] = totl_att['Data values_sort']
totl_adm['Admission share %'] = ((totl_adm['Total admissions Wales']/ totl_att['Data values_sort']) *100).round(1)
# totl_adm

#To get the total attendance for BCUHB, we add up the three major sites FROM #4 ED
attendance_target = attendance_target[attendance_target['Data description'] == 'Total attendances']
attendance_target = attendance_target.groupby('Date')[['Data values_sort']].sum()

attendance_target = attendance_target.reset_index()
attendance_target['Date_parsed'] = pd.to_datetime(attendance_target['Date'],format='%B %Y')
attendance_target = attendance_target.sort_values('Date_parsed')

#TO GET BCUHB ADMISSION SHARE
totl_adm = totl_adm.sort_values('Date_parsed')
attendance_target.index = totl_adm.index
totl_adm['BCUHB total attendance'] = attendance_target['Data values_sort']
totl_adm['BCUHB admissions'] = (totl_adm['Admission share %']/100) * attendance_target['Data values_sort']
# totl_adm
# attendance_target
# total_att_m2.head()
died_in_ED = data_tp[data_tp['Data description'] == 'Died in the department']
died_in_ED = died_in_ED[['Date_parsed','Date', 'Data description', 'Data values_sort']]
died_in_ED = died_in_ED.sort_values('Date_parsed')
died_in_ED.index = totl_adm.index
# died_in_ED
totl_adm_pro = pd.merge(totl_adm,died_in_ED, on=['Date_parsed','Date'], how='inner')
totl_adm_pro = totl_adm_pro.rename(columns = {'Data description':'Data description (Wales)'})
totl_adm_pro['Died in ED share % (BCUHB)'] = (totl_adm_pro['Data values_sort'] / totl_adm_pro['Total attendances Wales'])*100
totl_adm_pro['Total died (BCUHB)'] = ((totl_adm_pro['Died in ED share % (BCUHB)']/100) * totl_adm_pro['BCUHB total attendance']).round()
print(totl_adm_pro)

#6
#6 DISCHARGE:>
data = pd.read_csv('raw/Social_care_councils/delayed-hospital-discharges-total-pathway-of-care-delays-and-total-days-delayed-april-2023-onwards-v11-en-gb.csv',low_memory=False)
#Filtering
lhb_data = data[data['Local health board'] == 'Betsi Cadwaladr']
lhb_data = lhb_data[lhb_data['Local authority of residence'] == 'Wales']
lhb_data = lhb_data[lhb_data['Reason for delay'] == 'Total']
lhb_data['Date_parsed'] = pd.to_datetime(lhb_data['Date'], format='%B %Y')
lhb_data = lhb_data[lhb_data['Date'].str.contains('2026')]
lhb_data_patients = lhb_data[lhb_data['Data description']=='count of delays']
lhb_data_patients = lhb_data_patients[['Date_parsed','Date','Local health board','Data description','Data values_sort']]

lhb_data_days = lhb_data[lhb_data['Data description']=='count of days delayed']
lhb_data_days = lhb_data_days[['Date','Local health board','Data description','Data values_sort']]
# lhb_data_days
lhb_patients_days = pd.merge(lhb_data_patients, lhb_data_days, on=['Date','Local health board'], how='inner')
lhb_patients_days['Mean days delayed'] = lhb_patients_days['Data values_sort_y']/lhb_patients_days['Data values_sort_x']
# lhb_patients_days
actual_days_mn = {
    'January 2026':31,
    'Febuary 2026':28,
    'March 2026':31,
    'April 2026':30,
    'May 2026':31,
    'June 2026':30
}
days_mn = pd.Series(actual_days_mn, name='Actual days (month)')
days_mn = days_mn.reset_index()
days_mn = days_mn.rename(columns = {'index':'Date'})

lhb_patients_days = lhb_patients_days.sort_values('Date_parsed')
# 
lhb_patients_days.index = days_mn.index
lhb_patients_days['Actual days in month'] = days_mn['Actual days (month)']
lhb_patients_days['Patients entering a delay'] = (lhb_patients_days['Data values_sort_x']*lhb_patients_days['Actual days in month'])/lhb_patients_days['Mean days delayed']

#Patients entering a delay / BCUHB admissions 
lhb_patients_days['Share of admitted patients delayed %'] = (lhb_patients_days['Patients entering a delay'] / totl_adm_pro['BCUHB admissions']) * 100
print(lhb_patients_days)