import csv
from collections import defaultdict
import heapq
import sys

#pdf imports
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.validators import Auto
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.platypus import SimpleDocTemplate, Paragraph


def getDiaperPoopEstimation(user = 'all'):
    '''
    Converting values into meaningful ranges
    '''
    range_vals = ["less than 3", "3 - 6", "6 - 9", "9 - 12", "12 - 15", "15 or more"]
    poopcount = {_:0 for _ in range_vals}

    if user == 'all':
        for row in agg_data:
            if row["How many poopy diapers do you estimate since your last entry?"] == '':
                continue
            rval = range_vals[min(int(row["How many poopy diapers do you estimate since your last entry?"])//3, 5)]
            poopcount[rval] += 1
    else:
        for row in users[user]:
            if row["How many poopy diapers do you estimate since your last entry?"] == '':
                continue
            rval = range_vals[min(int(row["How many poopy diapers do you estimate since your last entry?"])//3, 5)]
            poopcount[rval] += 1
    return poopcount

def getGeneralStats(query = None, user = "all"):
    '''
    Can get the general stats of a uniform query/question
    '''
    if not query:
        return None
    data = defaultdict(int)

    if user == 'all':
        for row in agg_data:
            data[row[query]] += 1
    else:
        for row in users[user]:
            data[row[query]] += 1
    return data

def getRelativeStats(rel_query= "default", query = None, user = "all"):
    '''
    Can get the relative stats of a query with respect to 
    another query most usually the sick or not query. Sickness is determined
    by "Any GI distress" usually but can also be an aggregate of multiple queries 
    with any being yes considered the baby sick
    '''
    if not query:
        return None
    if rel_query == "default":
        rel_query = "Any GI distress?"
    elif rel_query == "all":
        all_query = ["Any sick days or days out of daycare?", "Any GI distress?", "Any allergies this week?", "Any antibiotics this week?"]
    
    healthy_stats = defaultdict(int)
    sick_stats = defaultdict(int)

    if user == "all":
        req_data = agg_data
    else:
        req_data = users[user]
    
    for row in req_data:
        if rel_query != "all":
            if row[rel_query] == "Yes":
                sick_stats[row[query]] += 1
            elif row[rel_query] == "No":
                healthy_stats[row[query]] += 1
        else:
            health_state = "No"
            for cur_query in all_query:
                if row[cur_query] == "Yes":
                    health_state = "Yes"
                    break
            if health_state == "Yes":
                sick_stats[row[query]] += 1
            else:
                healthy_stats[row[query]] += 1
    
    #normalize the stats
    tot_yes = sum(sick_stats.values())
    tot_neg = sum(healthy_stats.values())
    print ("THISS",tot_yes, tot_neg)
    if tot_yes == 0:
        return "No sick cases"
    elif tot_neg == 0:
        return "No healthy cases"
    sick_stats = {x: round(sick_stats[x] * 100/tot_yes,1) for x in sick_stats.keys()}
    healthy_stats = {x: round(healthy_stats[x] * 100/tot_neg, 1) for x in healthy_stats.keys()}
    print (sick_stats, healthy_stats) 
    return sick_stats, healthy_stats#pass it as it is and show this in bar chart

def getCombinedBabyFeedMethod(query = ["What is your breastfeeding feeding mode?","How did you feed your baby breast milk?"], user = "all"):
    '''
    Combines past and present version of the same question into one data set
    '''
    if user == "all":
        req_data = agg_data
    else:
        req_data = users[user]

    #Has mapping of previous option to current option
    change_mappings = {"Exclusive feeding at the breast" : "Exclusively at the breast", "Some feeding at the breast, some feeding expressed (pumped) milk": "Partially at the breast and partially using a bottle"}
    
    babyfeedmethod = defaultdict(int)
    for row in req_data:
        for cur_query in query:
            if row[cur_query] in change_mappings:
                babyfeedmethod[change_mappings[row[cur_query]]] += 1
            elif row[cur_query] == '':
                continue
            else:
                babyfeedmethod[row[cur_query]] += 1

    print ("AA",babyfeedmethod)
    return babyfeedmethod

def runTests():
    '''
    Runs multiple tests to verify correctness of data
    '''
    print (users.keys())

    colors = getColorStats()
    print (colors)
    colors_elauren = getColorStats("elaurenjohnson@gmail.com")
    print (colors_elauren)

    for user in users.keys():
        print (user, getColorStats(user))

    query1 = "How many poopy diapers do you estimate since your last entry?"
    print (query1, getGeneralStats(query1))
    query2 = "What was the consistency of the stool?"
    print (query2, getGeneralStats(query2))
    #print (query2, getGeneralStats(query2, "elaurenjohnson@gmail.com"))
    print (query2, getGeneralStats(query2, "frankie.goldstone@gmail.com"))

    query3 = "What was your baby's diet today?"
    print (getRelativeStats(query = query3))
    print (getRelativeStats(rel_query = "all", query = query3))
    print (getRelativeStats(query = query3, user = "frankie.goldstone@gmail.com"))

    print (getCombinedBabyFeedMethod())


def add_legend(draw_obj, chart, data):
    '''
    Add legend(the color labels below the chart)
    '''
    legend = Legend()
    legend.alignment = 'right'
    legend.x = -30
    legend.y = 60
    # #print ('here', legend.colorNamePairs, type(legend.colorNamePairs))
    # for i in range(len(chart.slices)):
    #     print (chart.slices[i].strokeColor)
    legend.colorNamePairs = Auto(obj=chart)
    #print ('here', legend.colorNamePairs[0], type(legend.colorNamePairs))
    draw_obj.add(legend)

def pie_chart_with_legend(data, my_title):
    '''
    Create a pie chart with the legend
    '''
    drawing = Drawing(width=500, height=250)
    my_title = String(125, 230, my_title, fontSize=18)
    pie = Pie()
    pie.sideLabels = True
    pie.x = 150
    pie.y = 95

    #make '' data or not inputted data as 'Not inputted'
    if '' in data.keys():
        data['Not inputted'] = data['']
        del data['']

    if len(data) > 9:
        data_keys = heapq.nlargest(9, data.items(), key = lambda i:i[1])
    else:
        data_keys = data.items()

    data_keys = sorted(data_keys, key = lambda x:x[1], reverse = True)
    print (data_keys)
    print (data)
    pie.data = list(sorted(data.values(), reverse = True))
    print (pie.data)

    tsum = sum(pie.data)
    if len(pie.data) > 9:
        pie.data = pie.data[:9]
    else:
        pie.data = pie.data

    #pie.labels = [str(round(val * 100/tsum,1)) for val in label_data]
    tsum = sum([x[1] for x in data_keys])
    data_keys = [(key, round(value*100/tsum, 1)) for key,value in data_keys]
    pie.labels = [_[0] for _ in data_keys]
    print (pie.labels)
    pie.slices.strokeWidth = 0.5
    drawing.add(my_title)
    drawing.add(pie)
    add_legend(drawing, pie, [_[0] for _ in data_keys])
    return drawing, data_keys

def bar_chart(sick_data, healthy_data, my_title):
    '''
    Create a bar chart
    '''
    data = [[], []]
    drawing = Drawing(width = 500, height = 280)
    my_title = String(10, 255, my_title, fontSize=18)
    all_labels = set(sick_data.keys()).union(set(healthy_data.keys()))
    print (all_labels)
    all_labels = list(all_labels)
    print (all_labels)
    for label in all_labels:
        if label in sick_data:
            data[0].append(sick_data[label])
        else:
            data[0].append(0)
        if label in healthy_data:
            data[1].append(healthy_data[label])
        else:
            data[1].append(1)
    bc = VerticalBarChart()
    bc.x = 0
    bc.y = 90
    bc.height = 125
    bc.width = 500
    bc.data = data
    #bc.strokeColor = colors.black
    bc.valueAxis.valueMin = 0
    bc.valueAxis.valueMax = max(max(sick_data.values()), max(healthy_data.values()))
    bc.valueAxis.valueStep = 10
    bc.categoryAxis.labels.boxAnchor = 'ne'
    bc.groupSpacing = 15
    bc.categoryAxis.labels.dx = 15
    bc.categoryAxis.labels.dy = -2
    bc.categoryAxis.labels.angle = 20
    #show '' as not inputted
    for i in range(len(all_labels)):
        if all_labels[i] == '':
            all_labels[i] = 'Not inputted'
    bc.categoryAxis.categoryNames = all_labels
    drawing.add(my_title)
    drawing.add(bc)
    return drawing

def makeConsistencyPieChart(elements, user):
    '''
    Create a pie chart object specificly for consistency of stool
    '''
    styles = getSampleStyleSheet()
    
    data = getGeneralStats("What was the consistency of the stool?", user)
    my_title = "Stool Consistency Distribution"
    chart, data_per = pie_chart_with_legend(data, my_title)
    elements.append(chart)
    print ('thisss', data_per)
    after_text = ["\nThis pie chart shows the distribution of stool consistency, with these being the percentage of the most significant characteristics: "]
    for i, (key, val) in enumerate(data_per, start = 1):
        after_text.append(str(i) + ")" + str(key) + ":" + str(val) + "% ")
    ptext = Paragraph("".join(after_text), styles["Normal"])
    elements.append(ptext)

def makeInferredConsistencyBarChart(elements, user):
    '''
    Create a relative bar chart object specificly for consistency of stool
    '''
    styles = getSampleStyleSheet()
    
    sick_data, healthy_data = getRelativeStats(query = "What was the consistency of the stool?", user =user)
    print (sick_data)
    print (healthy_data)
    my_title = "Comparison of stool consistency w.r.t sick and healthy observations"
    chart = bar_chart(sick_data, healthy_data, my_title)
    elements.append(chart)
    after_text = "This bar chart shows the side by side comparison of the consistency of the stool observed in days where baby was recorded to be in distress(sick) or without distress(healthy). Sick days are recorded as in the RED bar while healthy days are shown in the GREEN bar. "
    ptext = Paragraph(after_text, styles["Normal"])
    elements.append(ptext)

def makeColorPieChart(elements, user):
    '''
    Create a pie chart object specificly for color of stool
    '''
    styles = getSampleStyleSheet()
    
    data = getGeneralStats("What was the color of the stool?", user)
    my_title = "Stool Color Distribution"
    chart, data_per = pie_chart_with_legend(data, my_title)
    elements.append(chart)
    after_text = ["This pie chart shows the distribution of stool color, with these being the percentage of the most significant characteristics: "]
    for i, (key, val) in enumerate(data_per, start = 1):
        after_text.append(str(i) + ")" + str(key) + ":" + str(val) + "% ")
    ptext = Paragraph("".join(after_text), styles["Normal"])
    elements.append(ptext)

def makeInferredColorBarChart(elements, user):
    '''
    Create a relative bar chart object specificly for color of stool
    '''
    styles = getSampleStyleSheet()
    
    sick_data, healthy_data = getRelativeStats(query = "What was the color of the stool?", user= user)
    print (sick_data)
    print (healthy_data)
    my_title = "Comparison of stool color w.r.t sick and healthy observations"
    chart = bar_chart(sick_data, healthy_data, my_title)
    elements.append(chart)
    after_text = "This bar chart shows the side by side comparison of the color of the stool observed in days where baby was recorded to be in distress(sick) or without distress(healthy). Sick days are recorded as in the RED bar while healthy days are shown in the GREEN bar. "
    ptext = Paragraph(after_text, styles["Normal"])
    elements.append(ptext)

def makePoopEstimationPieChart(elements, user):
    '''
    Create a pie chart object specificly for number of poop estimated
    '''
    styles = getSampleStyleSheet()
    
    data = getDiaperPoopEstimation(user)
    my_title = "Number of Poopy Diaper Estimation"
    chart, data_per = pie_chart_with_legend(data, my_title)
    elements.append(chart)
    after_text = ["This pie chart shows the distribution of range of poopy diaper estimations, with these being the percentage of the most significant characteristics: "]
    for i, (key, val) in enumerate(data_per, start = 1):
        after_text.append(str(i) + ")" + str(key) + ":" + str(val) + "% ")
    ptext = Paragraph("".join(after_text), styles["Normal"])
    elements.append(ptext)

def makeCombinedBabyFeedPieChart(elements, user):
    '''
    Create a pie chart object specificly for method of feeding baby
    This method is special that it combines data from 2 versions of sample
    and aggregates them together
    '''
    styles = getSampleStyleSheet()
    print ("SUNJFSD", user)
    data = getCombinedBabyFeedMethod(user = user)
    my_title = "Baby Feed Method Distribution"
    print ('the data', data)
    chart, data_per = pie_chart_with_legend(data, my_title)
    elements.append(chart)
    print ('data_per', data_per)
    after_text = ["This pie chart shows the distribution of method of feeding baby, with these being the count of the most significant characteristics: "]
    for i, (key, val) in enumerate(data_per, start = 1):
        after_text.append(str(i) + ")" + str(key) + ":" + str(val) + " ")
    ptext = Paragraph("".join(after_text), styles["Normal"])
    elements.append(ptext)

def makeTitle(elements, my_title, user):
    '''
    Creates a title for the pdf
    elements: holds the drawing
    '''
    drawing = Drawing(width = 500, height = 45)
    my_title = String(5, 20, my_title + " - " + user, fontSize=24)
    drawing.add(my_title)
    elements.append(drawing)

def make_pdf(user):
    '''
    Creates the pdf for specific user
    user = 'All' is default
    '''
    doc = SimpleDocTemplate('Baby_Diaper_Report_' + user + '.pdf')
    
    elements = []
    my_title = "Baby Diaper Report"
    makeTitle(elements, my_title, user)
    makeColorPieChart(elements, user)
    makeInferredColorBarChart(elements, user)
    makeConsistencyPieChart(elements, user)
    makeInferredConsistencyBarChart(elements, user)
    makePoopEstimationPieChart(elements, user)
    makeCombinedBabyFeedPieChart(elements, user)

    doc.build(elements)


if __name__ == "__main__":
    
    users = {}
    agg_data = []

    with open('generatedBy_react-csv-7.csv', newline ='') as csvfile:
        reader = csv.DictReader(csvfile)
        for i,row in enumerate(reader):
            if row["sampleBarcodeId"][0] != 'B':
                continue
            if row["email"] not in users:
                users[row["email"]] = []
            users[row["email"]].append(row)
            agg_data.append(row)
    
    #runTests()
    if len(sys.argv) == 1:
        user = "all"
    else:
        user = sys.argv[1]
    make_pdf(user)
