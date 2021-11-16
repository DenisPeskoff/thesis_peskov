import json
import pandas as pd
import matplotlib.pyplot as plt
from plotnine import *
import jsonlines
from collections import defaultdict, Counter
from pandas.api.types import CategoricalDtype
import warnings
warnings.filterwarnings('ignore')

kROOT_DIR = "2020_acl_diplomacy"
kONE_COL = 2.5
kTWO_COL = 5.3

#specify for figure 2.
GAME_NAME = "BetaTest"

def datadir(filename):
    return "%s/data/%s" % (kROOT_DIR, filename)

def gfxdir(filename):
    return "%s/auto_fig/%s" % (kROOT_DIR, filename)


#reformatted the messaging tallying code to work with the simplified data format, but need to figure out efficient way to integrate game outcome tallies.   Likely just upload it independently.
def plot_game_lies(game_dir, filename, player_focus, year_focus, victory_season="winter"):
    joined = []

    # Read game text
    for fold in ["train", "dev", "test"]:
        with jsonlines.open(datadir("%s/%s.txt" % (game_dir, fold)), 'r') as reader:
            joined += list(reader)
            
    # Read supply centers
    counts = defaultdict(Counter)
    players = set()
    with open(datadir("%s/SupplyCenters.json" % game_dir)) as file:
        data = json.load(file)
        for key in sorted(data.keys()):
            year, season = key.split("_")
            year = int(year) % 1900
            if victory_season and victory_season != season:
                continue

            for country in data[key]:
                print(year, country, season)
                counts[(year, season, country.lower())]["Victory Points"] = int(data[key][country])
                players.add(country.lower())

    #loop through the messages, while skipping irrelevant season/years
    for index, message in enumerate(joined):
        year = int(message['year']) % 1900
        season = message['season']
        sender = message['sender'].lower()
        receiver = message['receiver'].lower()

        counts[(year, season, sender)]["Total_Counts"] += 1
        
        if message['sender_annotation']:
            counts[(year, season, sender)]["Send_Pos_Counts"] += 1
        else:
            counts[(year, season, sender)]["Send_Neg_Count"] += 1
            if message["receiver_annotation"] == True:
                counts[(year, season, sender)]["Deceived their Victim"] += 1


        if message['receiver_annotation'] == True:
            counts[(year, season, receiver)]["Rec_Pos_Counts"] += 1
            if message["sender_annotation"] == False:
                counts[(year, season, receiver)]["Victim Fell for Lie"] += 1
        elif message["receiver_annotation"] == False: # Distinguishing from null
            counts[(year, season, receiver)]["Rec_Neg_Counts"] += 1
            if not message['sender_annotation']:
                counts[(year, season, receiver)]["Victim Caught a Lie"] += 1

    columns = set()
    for key in counts:
        for statistic in counts[key]:
            # Bit of a hack to only print some statistics
            if "_" not in statistic:
                columns.add(statistic)

    print ("TEST", columns)
    data = defaultdict(list)
    for year, season, player in counts:
        for statistic in columns:
            data["Year"].append(int(year) % 1900)
            data["Season"].append(season)
            data["Player"].append(player.capitalize())
            data["Statistic"].append(statistic)
            key = (year, season, player)
            if key in counts:
                data["Value"].append(counts[key][statistic])
            else:
                data["Value"].append(0)

    for ii in data:
       assert len(data[ii]) == len(data["Player"]), "%s is not same length"

    final_data = pd.DataFrame(data)

    player_order = sorted(list(set(final_data['Player'])))
    final_data['Player'] = pd.Categorical(final_data['Player'], player_order, ordered=True)
    final_data["Value"]=final_data[["Value"]].apply(pd.to_numeric)

    final_data["Turn_Filter"] = 0.25

    if player_focus:
        final_data["Player_Filter"] = 90        
        final_data.loc[final_data.Player == player_focus, "Player_Filter"] = 100
        
    final_data.loc[final_data.Year == year_focus, "Turn_Filter"] = 1.0
    max_year = max(final_data["Year"])
    
    #final_data["1900_year"] = [y for y in range(1900, 1910)]
    
    
    print(final_data.head())

    #plotting code
    for year in range(1, max_year + 1):
        print("Year %i of %i" % (year, max_year))
        final_data["Year_Filter"] = 1.0
        final_data.loc[final_data.Year > year, "Year_Filter"] = 0.0
        lie_visualization = (ggplot(final_data) +
                             aes(x= 'Year', y='Value', fill = 'Player', order="Player") #, alpha="Year_Filter")
                             + labs( x= "Turn (Year)", y = "Count")
                             +theme_light()
                             +theme(panel_grid =element_blank(), legend_position='bottom')
                             +scale_fill_manual(["firebrick", "darkblue", "skyblue", "k", "seagreen", "darkmagenta", "gold"])
                             +scale_x_discrete(labels = ["'01", "'02", "'03", "'04", "'05", "'06", "'07", "'08", "'09", "'10"], limits = ["'01", "'02", "'03", "'04", "'05", "'06", "'07", "'08", "'09", "'10"])
                             +geom_col()
                             +facet_wrap("Statistic", ncol = 1, scales="free_y")
                             +guides(
                                 fill=guide_legend(title='', ncol=3)
                                 )
                                                   
                             
                             #+scale_x_continuous(labels = ["'01", "'02", "'03", "'04", "'05", "'06", "'07", "'08", "'09", "'10"])
                             # + theme(text=element_text(size=35), axis_text = element_text(size=35), legend_text=element_text(size=20), legend_title=element_text(size=25))
                             )

        lie_visualization.save(gfxdir("%s_%i.pdf" % (filename, year)), width=kONE_COL, height=3)

    if player_focus != '':
        player_focus = lie_visualization + aes(alpha="Player_Filter")
        player_focus.save(gfxdir("%s_player.pdf" % filename), width=kONE_COL, height=4)
    else:
        lie_visualization.save(gfxdir("%s.pdf" % filename), width=kONE_COL, height=4)
        

    year_focus = lie_visualization + aes(alpha="Year_Filter")
    year_focus.save(gfxdir("%s_year.pdf" % filename), width=kONE_COL, height=4)

    return final_data




#reformatted the messaging tallying code to work with the simplified data format, but need to figure out efficient way to integrate game outcome tallies.   Likely just upload it independently.
def makeF1():

    #open existing train/dev/splits for BetaGame
    with jsonlines.open(datadir('DiplomacyGame1/train.txt'), 'r') as reader:
        train = list(reader)
    with jsonlines.open(datadir('DiplomacyGame1/dev.txt'), 'r') as reader:
        dev = list(reader)
    with jsonlines.open(datadir('DiplomacyGame1/test.txt'), 'r') as reader:
        test = list(reader)

    #join the train/dev/test together for full game.
    joined = train+dev+test
            
    #create DF for plotnine
    storage = pd.DataFrame(columns=('Season', 'Player', 'Send_Pos_Counts', 'Send_Neg_Counts', 'Rec_Pos_Counts', 'Rec_Neg_Counts','Successful Lies', 'Believed Lies', 'Perceived Lies', 'Total Counts'))

    sanity, empty_count, total_count = 0, 0, 0
    send_pos_count, send_neg_count = 0,0
    rec_pos_count, rec_neg_count = 0,0
    successful_lies, believed_lies, perceived_lies = 0, 0, 0
    season_counter,total_season_counter = 0, 0

    #loop through each player, for each year, for each season and tally various types of lies/truths
    for p_index, player in enumerate(['italy', 'germany','austria','russia','england','turkey', 'france']):
        season_counter = 1 # to be updated.  plotting currently depends on season index %3 hence this choice.
        for y_index, year in enumerate(str(x) for x in range(1901, 1911)):
            #for each season
            for s_index, season in enumerate(['Spring', 'Fall', 'Winter']):
                
                #loop through the messages, while skipping irrelevant season/years
                for index, message in enumerate(joined):
                    
                    #skip if wrong year
                    if message['year'] != year:
                        continue
                    else:
                        #skip if wrong season within the year
                        if message['season'] != season:
                            continue
                    #tally where the player is the sender
                    if message['sender'] == player:
                        total_count+=1
                        if message['sender_annotation'] == True:
                            send_pos_count +=1
                            if message['receiver_annotation'] == False:
                                pass
                        elif message['sender_annotation'] == False:
                            send_neg_count+=1
                            if message['receiver_annotation'] == False:
                                pass#print("BOTH FALSE", id_match)
                            elif message['receiver_annotation'] == True:
                                successful_lies +=1
                    #tally where player is receiver
                    elif message['receiver'] == player:
                        if message['receiver_annotation'] == True:
                            rec_pos_count+=1
                            if message['sender_annotation'] == False:
                                believed_lies+=1
                        elif message['receiver_annotation'] == False:
                            rec_neg_count+=1
                            if message['sender_annotation'] == False:
                                perceived_lies+=1

                #sum up over an entire year, append to dataframe, and reset counts
                if season == "Winter":
                    storage.loc[p_index+total_season_counter] = (season_counter, player, send_pos_count, send_neg_count, rec_pos_count, rec_neg_count, successful_lies, believed_lies, perceived_lies, total_count)
                    total_season_counter+=1
                    send_pos_count, send_neg_count = 0,0
                    rec_pos_count, rec_neg_count = 0,0
                    successful_lies, believed_lies, perceived_lies = 0, 0, 0
                    total_count = 0
                season_counter+=1

                    
    supply_center = pd.DataFrame(columns=('Year', 'Player', 'Supply Centers' ))
    season_counter, storage_counter = 1, 0
    with open(datadir('DiplomacyGame1/SupplyCenters.json')) as f:
        data = json.load(f)
        for key in sorted(data.keys()):
            #current visualization is only for winter season.  Can be changed if needed.
            if key.find('winter') != -1:
                relevant_season = data[key]
                #loop through each country
                for index, country_key in enumerate(relevant_season.keys()):
                    print(country_key.lower(), relevant_season[country_key])
                    #offsetting by 3 to line up with message visualization, which is done by year, not by individual season
                    supply_center.loc[storage_counter] = (season_counter*3, country_key.lower(), relevant_season[country_key])
                    storage_counter+=1
                season_counter+=1
                    
                    
    #Not all of the below are necessarily graphed
    joint_supply = supply_center.rename(columns={"Supply Centers": "Data"})
    joint_supply['Type'] = "4. Victory Points"
        
    df1 = storage[['Season','Player','Total Counts']]
    df1['Type'] = "1. Total Messages Sent"
    df1 = df1.rename(columns={"Total Counts": "Data", "Season": "Year"})

    df2 = storage[['Season','Player','Send_Neg_Counts']]
    df2['Type'] = "2. Total Lies"
    df2 = df2.rename(columns={"Send_Neg_Counts": "Data", "Season": "Year"})

    df3 = storage[['Season','Player','Successful Lies']]
    df3['Type'] = "2. Successful Lies Made"
    df3 = df3.rename(columns={"Successful Lies": "Data", "Season": "Year"})

    df4 = storage[['Season','Player','Believed Lies']]
    df4['Type'] = "3. Lies Believed "
    df4 = df4.rename(columns={"Believed Lies": "Data", "Season": "Year"})

    df5 = storage[['Season','Player','Perceived Lies']]
    df5['Type'] = "4. Perceived Lies"
    df5 = df5.rename(columns={"Perceived Lies": "Data", "Season": "Year"})

    #need to re-integrate code for actions
    joint = df1.append(df3).append(df4).append(joint_supply)
    final_data =  joint[(joint['Year']==3)|(joint['Year']==6)|(joint['Year']==9)|(joint['Year']==12)|(joint['Year']==15)|(joint['Year']==18)|(joint['Year']==21) | (joint['Year']==24) | (joint['Year']==27)| (joint['Year']==30)]
    final_data.head()
    player_order = ['austria', 'england', 'france', 'germany', 'italy', 'russia', 'turkey']
    final_data['Player'] = pd.Categorical(final_data['Player'], player_order, ordered=True)
    final_data["Data"]=final_data[["Data"]].apply(pd.to_numeric)

    #plotting code
    lie_visualization = (ggplot(final_data) +
     aes( x= 'Year', y='Data',fill = 'Player', order="Player")
     +theme_light()
     + theme(panel_grid =element_blank())
     +scale_fill_manual(["firebrick", "darkblue", "skyblue", "k", "seagreen", "darkmagenta", "gold"])
     + labs(title = "Effect of Lies on Game Outcome", x= "Year", y = "Raw Count")
     + scale_x_discrete(labels = ["'01", "'02", "'03", "'04", "'05", "'06", "'07", "'08", "'09", "'10"])
     +geom_col()
     +facet_wrap("Type", ncol = 1, scales="free_y")
     + theme(text=element_text(size=35), axis_text = element_text(size=35), legend_text=element_text(size=20), legend_title=element_text(size=25))
    )

    lie_visualization.save(gfxdir('LieVisualization.pdf'), width=kONE_COL, height=3)

def makeF3():

    #redo to depend on only process jsonlines file (_data variation)

    train_data = jsonlines.open(datadir('train.jsonl'))
    all_messages= []
    for convo in train_data:
        all_messages.extend(convo['messages'])
    
    avg_len = []
    for message in all_messages:
        avg_len.append(len(message.split()))

    temp_dict = {'length': avg_len}
    plotnine_df = pd.DataFrame(data=temp_dict)

    
#    with open(datadir('train.txt'), 'w') as outfile:
#      avg_len = []
#      avg_q = []
#      #avg_sent = []
#      for message in json_lines_data:
#        #sent_count = nlp(message['message'])
#        #avg_sent.append(sum(1 for _ in sent_count.sents))
#        avg_q.append(message['message'].count("?")- message['message'].count("??"))#multiple question marks occur rarely.  And >2 question marks is insignifcant
#        avg_len.append(len(message['message'].split()))

    
    length_histogram =(ggplot(plotnine_df)
                       + aes('length')
                       + geom_histogram()
                       + stat_bin(bins=50)
#                       + scale_y_continuous(trans = "sqrt")
                       + labs(x= 'Word Count per Message', y='Frequency')
                       )

    length_histogram.save(gfxdir('LengthFrequency.pdf'), width=kONE_COL, height=2)




def makeFAppendix():
    with open(datadir('UserSurvey.csv')) as gfile:
        data = pd.read_csv(gfile)

            
    #convert into plotnine format of all itmes in one column
    storage = pd.DataFrame(columns=('Percentage', 'Type'))
    for index, item in enumerate(data['What is your gender?']):
        storage.loc[index] = (item, "Gender")
    total = len(storage)

    for index, item in enumerate(data['What is your age?']):
        storage.loc[index+total] = (item, "Age")

    total = len(storage)
    for index, item in enumerate(data['What is your highest level of education? (select the one in-progress if not complete)']):
        storage.loc[index+total] = (item, "Education")

    total = len(storage)
    for index, item in enumerate(data['How many Diplomacy games have you played?']):
        storage.loc[index+total] = (item, "Games")
    total = len(storage)


    diplo_storage = pd.DataFrame(columns=('Percentage', 'Type'))
    for index, item in enumerate(data['How good of a liar are you?']):
        diplo_storage.loc[index+total] = (item, "Lying")

    total = len(diplo_storage)
    for index, item in enumerate(data['Can you tell when others are lying?']):
        diplo_storage.loc[index+total] = (item, "Perception")

    user_demo = (ggplot(storage) +
                 aes(x= 'Type', fill = "Percentage")
                 + theme_light()
                 + geom_bar()
                + labs( y= "Percentage",)
                 + facet_wrap("Type", ncol=1, scales="free")
                 #+ facet_grid(facets="Count ~ Type", scales="free")#, scales="free")
                 + theme(text=element_text(size=18),  legend_text=element_text(size=14), legend_position='top', legend_title = element_blank(), axis_text_y = element_blank())
                 )


    user_demo.save(gfxdir('UserDemographics.pdf'), width=kONE_COL, height=3)


    diplo_demo = (ggplot(diplo_storage) +
                  aes(x= 'Type', fill = "Percentage")
                  + theme_light()
                  + theme(panel_grid =element_blank(), axis_ticks_major_y = element_blank())
                  + geom_bar()
                  + labs( y= "Percentage",)
                  +facet_wrap("Type", nrow = 1, scales="free",)
                  + theme(text=element_text(size=18),  legend_text=element_text(size=14), legend_position='top', legend_title = element_blank(), axis_text_y = element_blank())
                  )

    diplo_demo.save(gfxdir('DiploDemographics.pdf'), width=kONE_COL, height=3)

def makeF4():

    # Don't hard code data in python, make this readable from data files
  
    storage = pd.DataFrame(columns=('Data', 'Type'))
    storage.loc[0] = (10979., "Straightforward")
    storage.loc[1] = (501., "Cassandra")
    storage.loc[2] = (480., "Deceived")
    storage.loc[3] = (65., "Caught")

    storage["Type"] = pd.Categorical(storage["Type"], ["Straightforward", "Deceived", "Cassandra", "Caught"])

    quartile_chart = (ggplot(storage) +
                 aes(x= 'Type', y = 'Data', fill = 'Type',)
                 + theme_light()
                + labs( y= "Train Counts", x='')
                 + geom_col(position = 'stack')                      
                      #+ labs( y= "Data",)
                      #+ facet_wrap("Type", ncol=2, scales="free")
                 #+ facet_grid(facets="Count ~ Type", scales="free")#, scales="free")
                      +scale_y_continuous(trans = "sqrt")
                + theme(axis_text_x = element_blank(), legend_position='top')
# legend_title = element_blank(), legend_position='top', legend_text=element_text(size=14)
                  + guides(
                      fill=guide_legend(title='', ncol=2)
                      )
                 )
    quartile_chart.save(gfxdir('Distribution.pdf'), width=kONE_COL, height=2)

def makeF5():
    
    # Don't hard code data in python, make this readable from data files
    
    storage = pd.DataFrame(columns=('Data', 'Outcome'))
    storage.loc[0] = (2055., "Both Correct")
    storage.loc[1] = (147., "Model Correct")
    storage.loc[2] = (132., "Human Correct")
    storage.loc[3] = (141., "Both Wrong")
    
    
    quartile_chart = (ggplot(storage) +
                      aes(x= 'Outcome', y = 'Data', fill = 'Outcome',)
                      + theme_light()
                      + geom_col(position = 'stack')
                      + labs( y= "Count of Predictions",)
                      + coord_flip()                       
                      + scale_y_continuous(trans = "sqrt")
                      #+ labs( y= "Data",)
                      #+ facet_wrap("Type", ncol=2, scales="free")
                      #+ facet_grid(facets="Count ~ Type", scales="free")#, scales="free")
                      #+scale_y_continuous()
                      + theme(legend_position='top', legend_title = element_blank())
                      )
    quartile_chart.save(gfxdir('ModelHumanComparison.pdf'), width=kONE_COL, height=3)


def makeF6(dataset, languages, ha, nudge_y):
    data = []
    with open(datadir('results_presentation.txt')) as f:
        for line in f:
            segments = line.strip().split('\t')
            temp = []
            data.append(segments)

    models = ['Random', 'Majority Class',  'Harbingers', 'Bag of Words', 'Bag of Words+Power', 'LSTM',
              'Context LSTM', 'Context LSTM+Power',  'Human' ]
    models = models[::-1]
    tasks = ['Macro F1', 'Lie F1']
    d = defaultdict(list)
    flag = False
    for i in range(len(models)):
        if i == 5:
            flag = True
        for j in range(len(tasks)):
            for k in range(len(languages)):
                #drop last human one since it's n/a
                val = data[i][j * len(tasks) + k]
                if val != "NA":
                    d['Models'].append(models[len(models) - i - 1])
                    d['Languages'].append(languages[k])
                    d['Task'].append(tasks[j])

                    if flag:
                        temp = 0
                    else:
                        temp = float(val)
                    d['F1'].append(temp)
                    if temp != 0.0:
                        d['Label'].append("%0.1f" % temp)
                    else:
                        d['Label'].append("")

    df = pd.DataFrame(data=d)
    # print(df)

    model_cat = CategoricalDtype(categories=models, ordered=True)
    df['Models_Cat'] = df['Models'].astype(str).astype(model_cat)
    task_cat = CategoricalDtype(categories=tasks, ordered=True)
    df['Task_Cat'] = df['Task'].astype(str).astype(task_cat)
    language_cat = CategoricalDtype(categories=languages, ordered=True)
    df['Languages_Cat'] = df['Languages'].astype(str).astype(language_cat)

    p = ggplot(aes(x='Models_Cat', y='F1'), data=df) \
        + geom_bar(stat='identity', fill="#FFD520", colour="#500000", size=0.5, show_legend=False) \
        + coord_flip() \
        + geom_text(aes(label='Label',  vjust=0, size=5), ha=ha, nudge_y=nudge_y, show_legend=False) \
        + facet_grid(('Languages_Cat', 'Task_Cat'), labeller=labeller(multi_line=False), scales="free") \
        + theme(axis_title_y=element_blank(), axis_title_x=element_blank(), panel_spacing_x=.03, panel_spacing_y=.05)
    p.save('2020_acl_diplomacy/auto_fig/' + dataset + '.pdf', width=kTWO_COL, height=4)

#+ scale_y_continuous(limits=(0, upper), breaks=breaks)


if __name__ == "__main__":
    #game1 = plot_game_lies("DiplomacyGame1", "game_lies", "", 10)
    #makeF3()
    #makeF4()
    #makeF5()
    makeF6('results_presentation', ['Actual Lie', 'Suspected Lie'], 'right', -1)
    #makeFAppendix()
