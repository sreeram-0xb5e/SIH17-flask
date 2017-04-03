from flask import Flask, redirect, url_for, request
app = Flask(__name__)
import mysql.connector as mariadb
import datetime


# MACHINE LEARNING-------------------------------------------------------
from sklearn.cross_validation import KFold
from sklearn.linear_model import LinearRegression, Lasso, Ridge, ElasticNet, SGDRegressor
import numpy as np
#import pylab as pl
import pandas as pd

# calculating base score
def base_score(house_type,no_of_room,adultmembers,familyhead,caste,disability,literacy_gen):
    bs = 0
    # FIRST
    if (house_type is "kuchatype"):
        bs = bs + 0.5
    if(no_of_room <2):
        bs = bs + 0.5

    # SECOND
    if (adultmembers == 0):
        bs = bs+1

    #THIRD
    if (familyhead is "female"):
        bs = bs +1

    #FOURTH
    if (caste is "sc" or caste is "st"):
        bs = bs +1
    elif (caste is "obc"):
        bs = bs + 0.5
    else:
        bs = bs +0

    #FIFTH

    if (disability is 1):
        bs = bs +1

    #SIXTH
    if (literacy_gen is 1):
        bs = bs + 1

    return ((bs/6)*5)

#calculating the regression score

def regression_score(age,qual,emp_type):

    train_input = pd.read_csv('train_input.csv', sep=",", header = None)
    train_output = pd.read_csv('train_output.csv',sep=",",header = None)
    linreg = LinearRegression()
    linreg.fit(train_input,train_output)
    return linreg.predict([age,qual,emp_type])

def total_score (house_type,no_of_room,adultmembers,familyhead,caste,disability,literacy_gen,age,qual,emp_type):
    return (base_score(house_type,no_of_room,adultmembers,familyhead,caste,disability,literacy_gen) + regression_score(age,qual,emp_type))

#----------------------------------------------------------------------------------------------------------------
#QUERY RANKING

def query_regression_score(tcid,itype,category):

    train_input = pd.read_csv('1.csv', sep=",", header = None)
    train_output = pd.read_csv('2.csv',sep=",",header = None)
    linreg = LinearRegression()
    linreg.fit(train_input,train_output)
    return linreg.predict([tcid,itype,category])


#----------------------------------------------------------------
def decode(var):
        if isinstance(var,bytearray):
                return var.decode('utf-8')
        if isinstance(var,datetime.date):
                return str(var)
        if isinstance(var,int):
                return var
        if isinstance(var,str):
                return var

        return

def dictfetchall(cursor):
    desc = cursor.description
    return [dict(zip([col[0] for col in desc], map(decode,row)))
            for row in cursor.fetchall()]
#------------------------------------------------------------------


@app.route('/')
def success():
    return "Welcome!"

@app.route('/login',methods = ['POST','GET'])
def login():
    if request.method == 'POST':
        user = request.form['name']
        return "Welcome" + user

#-------------------Question ranking

@app.route('/qranking', methods = ['POST','GET'] )

def query_ranking ():
    mariadb_connection = mariadb.connect(host="172.104.51.13",user='smh2017', password='smh2017bro', database='SMH')


    # To Fetch the count of the questions

    cursor = mariadb_connection.cursor(prepared = True)
    cursor.execute("SELECT COUNT(id) FROM question")
    cp = dictfetchall(cursor)
    cursor.close()
    n = (cp[0]['COUNT(id)'])


    # To fetch the entire database as dictionary

    cursor = mariadb_connection.cursor(prepared = True)
    cursor.execute("SELECT * from question")
    data = dictfetchall(cursor)
    cursor.close()


    # copying the data into the local variable



    cursor = mariadb_connection.cursor(prepared = True)
    for i in range(0,int(n)):
        cursor.execute("SELECT tcid,type,category FROM question")
        local_data = dictfetchall(cursor)
        cursor.close()
        #qrs = query_regression_score(local_data[i]['tcid'],local_data[i]['type'],local_data[i]['category'])

        #cursor.execute("UPDATE question set score = ? WHERE id like ?"(qrs,i))
        #print ("Updated!")

    #cursor.close()
    #mariadb_connection.commit()
    #mariadb_connection.close()
    #return "Done!"
    return local_data[i]['tcid']
#-----------------------------------------------------------------------------------------------------------------

# CANDIDATE SELECTION

@app.route('/cselection/<lstate>', methods = ['POST','GET'] )
def candidate_selection(lstate):
    mariadb_connection = mariadb.connect(host="172.104.51.13",user='smh2017', password='smh2017bro', database='SMH')

    # To fetch the count of the candidate

    cursor = mariadb_connection.cursor(prepared = True)
    cursor.execute("SELECT COUNT(aadharno) FROM candidatex")
    cp = dictfetchall(cursor)
    cursor.close()

    n = (cp[0]['COUNT(aadharno)'])

    # To fetch the entire database as dictionary

    cursor = mariadb_connection.cursor(prepared = True)
    cursor.execute("SELECT * from candidatex")
    data = dictfetchall(cursor)
    cursor.close()

    #Copying the data to local variables

    aadhar_array=[]
    rank_array=[]



    for i in range(0,int(n)):
        aadhar_array.append((data[i]['aadharno']))

        cursor = mariadb_connection.cursor(prepared = True)
        cursor.execute("SELECT house_type,no_of_room,adultmembers,familyhead,caste,disability,literacy_gen,age,qual,emptype FROM candidatex")
        local_data = dictfetchall(cursor)
        cursor.close()

        #rank = total_score(local_data[0])

         #rank_array.append()

    #print (aadhar_array)


    for i in range(0,int(n)):
        ts = total_score(local_data[i]['house_type'],local_data[i]['no_of_room'],local_data[i]['adultmembers'],local_data[i]['familyhead'],local_data[i]['caste'],local_data[i]['disability'],local_data[i]['literacy_gen'],local_data[i]['age'],local_data[i]['qual'],local_data[i]['emptype'])
        rank_array.append(ts[0][0])


    for i in range(0,int(n)):
        for j in range (0,int(n)):
            if (rank_array[j] < rank_array[i]):
                temp = aadhar_array[i]
                aadhar_array[i] = aadhar_array [j]
                aadhar_array[j] = temp

                temp = rank_array[i]
                rank_array[i] = rank_array [j]
                rank_array[j] = temp

    print (rank_array)
    count = 1
    for i in range(0,int(n)):

        cursor = mariadb_connection.cursor(prepared = True)
        cursor.execute("UPDATE candidate SET rank = ? WHERE aadharno LIKE ?",(count,aadhar_array[i]))
        print ("Updated!")
        print (count )
        count = count + 1;
        cursor.close()


        # Query
        cursor = mariadb_connection.cursor(prepared = True)
        cursor.execute("SELECT aadharno,name,mobileno,rank FROM candidate WHERE state like ? ORDER BY RANK ASC",(lstate,))
        final_output = dictfetchall(cursor)
        cursor.close()

    mariadb_connection.commit()
    mariadb_connection.close()
    #print (final_output)
    edit = str(final_output)
    edit = edit.replace("'" , "\"")
    return edit

#-------------------------------------------------------------------------------
if __name__ == '__main__':
   app.run(host="0.0.0.0",debug = True)
