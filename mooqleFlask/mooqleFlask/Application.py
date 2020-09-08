from flask import Flask,render_template,url_for,request,redirect
from flask_mysqldb import MySQL
import nltk
from nltk.corpus import wordnet
import numpy as np
import yaml
import re
from Cryptodome.Cipher import AES


app = Flask(__name__)

#Configure db
db = yaml.full_load(open('db.yaml'))
app.config['MYSQL_HOST'] = db['mysql_host']
app.config['MYSQL_USER'] = db['mysql_user']
app.config['MYSQL_PASSWORD'] = db['mysql_password']
app.config['MYSQL_DB'] = db['mysql_db']

mysql = MySQL(app)

@app.route('/')

#calling the home page front-end
def index():
    
    return render_template("HomePage.html")

#call handle_data function once post is submitted
@app.route('/handle_data', methods=['POST'])

def handle_data():

    #Invalid message for user input
    InvalidMessage = "Unable to search due to invalid input"
    getOut = False
    
    #fixed key for the encryption
    key = 'abcdefghijklmnop'
    #variable to store the keyword entered by user
    keyword = request.form['uKeyword']
    #condition when user input nothing and press search button
    if(keyword == ""):
        return render_template("HomePage.html")
    #condition if user input any keyword
    else:
        #ignore all special character other than, alphabets, number or space
        keyword= re.sub('[^a-zA-Z0-9 ]',' ',keyword)
        #remove space infront and at the back of the string if it exist
        keyword=keyword.strip()

        #force keyword into lower caps
        keyword = keyword.lower()
        
        splitlist = []
        encryptedlist = []
        splitlist = keyword.split(' ')
        #this is to remove the common words
        Exclude = ["ourselves", "hers", "between", "yourself", "but", "again", "there", "about", "once", "during", "out", "very", "having", "with", "they", "own", "an", "be", "some", "for" , "do", "its", "yours", "such", "into", "of", "most", "itself", "other", "off", "is", "s", "am", "or", "who", "as", "from", "him", "each", "the", "themselves", "until", "below", "are", "we", "these", "your", "his", "through", "don", "nor", "me", "were", "her", "more", "himself", "this", "down", "should", "our", "their", "while", "above", "both", "up", "to", "ours", "had", "she", "all", "no", "when", "at", "any", "before", "them", "same", "and", "been", "have", "in", "will", "on", "does", "yourselves", "then", "that", "because", "what", "over", "why", "so", "can", "did", "not", "now", "under", "he", "you", "herself", "has", "just", "where", "too", "only", "myself", "which", "those", "i", "after", "few", "whom", "t", "being", "if", "theirs", "my", "against", "a", "by", "doing", "it", "how", "further", "was", "here", "than"]
        splitlist = np.setdiff1d(splitlist,Exclude)
        
        if(len(splitlist) == 0):
            return render_template("HomePage.html", InvalidMessage = InvalidMessage)
        elif(len(splitlist) == 1 and (splitlist[0] == " " or splitlist[0] == "")):
            return render_template("HomePage.html", InvalidMessage = InvalidMessage)
        
        else:
        #call cursor object
            cur = mysql.connection.cursor()

            #some list variables
            lists = []
            check = []
            removeWord=[]
            decryptedList =[]
            

            #check if there is more than 1 word in the string
            if len(splitlist) > 1:
                for x in range(len(splitlist)):
                    #store the ciphertext into a string called temp
                    Temp= str(encryptAES(key,splitlist[x]))
                    #convert string to a list
                    Temp = list(Temp)
                    #condition to convert '\\' into '\\\\' for database query
                    for i in range(len(Temp)):
                        if (Temp[i] == '\\'):
                            Temp[i] ='\\\\\\\\'
                        if(Temp[i] == '"'):
                            Temp[i] = '\\"'
                    #this is to delete the b'' where it is used as method of reading bytes by python        
                    del Temp[-1]
                    del Temp[0]
                    del Temp[0]
                    #to finally store all letters in list into a string
                    FinalString=""
                    result = FinalString.join(Temp)
                    #store the encrypted word into a list
                    encryptedlist.append(result)
                    
                    #clear out temp
                    Temp=[]
                #this query is to check through the database that have all the keyword the user input
                query = 'SELECT * FROM mooqledb.webcontent WHERE '
                query1 = '(text LIKE "%'+encryptedlist[0]+'%")'
                query = query + query1
                for x in range(1,len(encryptedlist)):
                    query = query + ' AND (text LIKE "%'+encryptedlist[x]+'%")' 
                
                #execute query
                resultValue = cur.execute(query)
                
                if resultValue > 0 :
                    wordToShow =[]
                    joinText =""
                    
                    #to retrieve all results from db
                    userDetails = cur.fetchall()
                    for row in userDetails:
                        decryptedList.append([row[0],row[1],row[2]])
                    for i in range(len(decryptedList)):
                        #access db "text" column
                        tempstrText = decryptedList[i][0]
                        tempstrURL = decryptedList[i][1]

                        #delete the byte reading code 
                        tempstrText = tempstrText[2:]
                        tempstrText = tempstrText[:-1]

                        #delete the byte reading code
                        tempstrURL = tempstrURL[2:]
                        tempstrURL = tempstrURL[:-1]
                        
                        #convert text to byte
                        tempstrText = bytes(tempstrText,'latin1')
                        tempstrText = tempstrText.decode('unicode-escape').encode('latin1')

                        #convert URL to byte
                        tempstrURL = bytes(tempstrURL,'latin1')
                        tempstrURL = tempstrURL.decode('unicode-escape').encode('latin1')

                        #decrypt the encrypted text
                        decrypted = decryptAES(key, tempstrText)
                        
                        #seperate decrypted word into list
                        contextList = decrypted.split()

                        #display in result page, where the contents of url is limited up to 65 words
                        if(len(contextList) > 65):
                            for j in range (len(contextList)):
                                for k in range (len(splitlist)):
                                    #condition to match keyword
                                    if (contextList[j] == splitlist[k]):
                                        if (j < (len(contextList)-60)):
                                            for l in range (0,60):
                                                wordToShow.append(contextList[j+l])
                                            #join the 60 words next to keyword
                                            joinText = " ".join(wordToShow)
                                        elif(j > (len(contextList)-60) and j < 60):
                                            for l in range (0,59-j):
                                                wordToShow.append(contextList[j+l])
                                            #join the 60 words next to keyword
                                            joinText = " ".join(wordToShow)
                                        else:
                                            for l in range (59,-1,-1):
                                                wordToShow.append(contextList[j-l])
                                            #join the 60 words before the keywords
                                            joinText = " ".join(wordToShow)
                                        #reset list so it wont have too much word
                                        wordToShow = []
                                        getOut = True
                                        break
                                if(getOut == True):
                                    getOut = False
                                    break
                        #condition where the length of the total contents in db is not more than 60 words
                        else:
                            joinText = " ".join(contextList)
                        
                        #variable to store the result of decrypted URL
                        decryptedURL = decryptAES(key,tempstrURL)
                        
                        #edit the list with new decrypted text
                        decryptedList[i][0] = joinText
                        decryptedList[i][1] = decryptedURL
                        counts = joinText.count(keyword)
                        decryptedList[i][2] = counts

                    #clear all variable or list
                    keyword=""
                    query=""
                    encryptedlist =[]
                    splitlist =[]
                    joinText=""
                    contextList=""
                    wordToShow=[]
                    decryptedURL =""
                    counts=''
                    tempstrText=""
                    tempstrURL=""

                    #sort the decryptedList based on count of the keyword
                    decryptedList.sort(key = lambda x:x[2], reverse=True)
                    return render_template('ReturnResult.html',decryptedList = decryptedList)
                else:
                    return render_template('NoResult.html')


            #if there only 1 word the user input we will find the synonyms of the word    
            else :
                wordToShow =[]
                joinText =""
                #finding the synoyms of the word
                lists.append(splitlist[0])
                for syn in wordnet.synsets(splitlist[0]) :
                    for l in syn.lemmas():
                        lists.append(l.name()) 

                sizecheck =3

                #removing underscore in list words
                for i in range(len(lists)):
                    word = lists[i]
                    word = list(word)
                    for j in range(len(word)):
                        if(word[j] == '_'):
                            word[j] = ' '
                    wordJoin=""
                    synonyms = wordJoin.join(word)
                    lists[i] = synonyms

                    
                #clear out synonyms variable
                synonyms =""
                #check for duplicates and set limit of synonyms to 4
                for s in lists:
                    if s not in removeWord:
                        if sizecheck == len(check):
                            break   
                        else :
                            #store the ciphertext into a string called temp
                            #s is the synonyms of the keyword
                            Temp= str(encryptAES(key,s))

                            #convert string to a list
                            Temp = list(Temp)

                            #condition to convert '\\' into '\\\\' for database query
                            for i in range(len(Temp)):
                                if (Temp[i] == '\\'):
                                    Temp[i] ='\\\\\\\\'
                                if(Temp[i] == '"'):
                                    Temp[i] = '\\"'
                            #this is to delete the b'' where it is used as method of reading bytes by python        
                            del Temp[-1]
                            del Temp[0]
                            del Temp[0]
                            #to finally store all letters in list into a string
                            FinalString=""
                            result = FinalString.join(Temp)
                            check.append(result)
                            
                            #clear out Temp
                            Temp =[]
                            #clear out result variable
                            result =""
                    removeWord.append(s) 
                

            #this query is to check through the database with the synonyms of the keyword
            query = 'SELECT * FROM mooqledb.webcontent WHERE '
            query1 = '(text LIKE "%'+check[0]+'%")'
            
            query = query + query1
            
            for x in range(1,len(check)):
                query = query + 'OR (text LIKE "%'+check[x]+'%")'
            resultValue = cur.execute(query)
            
            if resultValue > 0 :
                userDetails = cur.fetchall()
                for row in userDetails:
                    decryptedList.append([row[0],row[1],row[2]])
                for i in range(len(decryptedList)):
                    #access db "text" column
                    tempstrText = decryptedList[i][0]
                    tempstrURL = decryptedList[i][1]

                    #delete the byte reading code 
                    tempstrText = tempstrText[2:]
                    tempstrText = tempstrText[:-1]

                    #delete the byte reading code
                    tempstrURL = tempstrURL[2:]
                    tempstrURL = tempstrURL[:-1]
                    
                    #convert text to byte
                    tempstrText = bytes(tempstrText,'latin1')
                    tempstrText = tempstrText.decode('unicode-escape').encode('latin1')

                    #convert URL to byte
                    tempstrURL = bytes(tempstrURL,'latin1')
                    tempstrURL = tempstrURL.decode('unicode-escape').encode('latin1')

                    #decrypt the encrypted text
                    decrypted = decryptAES(key, tempstrText)
                    contextList = decrypted.split()

                    #to store the keyword into a list, then if an elements is a 2 word keyword, it will be seperated
                    tempThis = " ".join(removeWord)
                    tempThis = list(tempThis.split())

                    #display in result page, where the contents of url is limited up to 65 words
                    if(len(contextList) > 65):
                        for j in range (len(contextList)):
                            for k in range (len(tempThis)):
                                #condition to match keyword
                                if (contextList[j] == tempThis[k]):
                                    if (j < (len(contextList)-60)):
                                        for l in range (0,60):
                                            wordToShow.append(contextList[j+l])
                                        #join the 60 words next to keyword
                                        joinText = " ".join(wordToShow)
                                    elif(j > (len(contextList)-60) and j < 60):
                                        for l in range (0,59-j):
                                            wordToShow.append(contextList[j+l])
                                        #join the 60 words next to keyword
                                        joinText = " ".join(wordToShow)
                                    else:
                                        for l in range (59,-1,-1):
                                            wordToShow.append(contextList[j-l])
                                        #join the 60 words before the keywords
                                        joinText = " ".join(wordToShow)
                                    #reset list to empty so it will not have too many words    
                                    wordToShow = []
                                    getOut = True
                                    break
                            if(getOut == True):
                                getOut = False
                                break
                    #condition where the length of the total contents in db is not more than 60 words
                    else:
                        joinText = " ".join(contextList)

                    decryptedURL = decryptAES(key,tempstrURL)
                    #edit the list with new decrypted text
                    decryptedList[i][0] = joinText
                    decryptedList[i][1] = decryptedURL
                    counts = joinText.count(keyword)
                    decryptedList[i][2] = counts
                    
                #clear all variables and lists
                keyword=''
                removeWord = []
                query=""
                check = []
                tempstrText=""
                tempstrURL=""
                contextList=[]
                wordToShow=""
                joinText=""
                counts=''
                decrypted=""
                decryptedURL=""
                tempThis=[]

                #sort the decryptedList based on count of the keyword
                decryptedList.sort(key = lambda x:x[2], reverse=True)
                
                return render_template('ReturnResult.html',decryptedList = decryptedList)
            else:
                return render_template('NoResult.html')

#encryption function
def encryptAES(key, plaintext): 
    #initialise encryption using pycryptodome library
    #using AES, ECB
    cipher = AES.new(key.encode("utf8"), AES.MODE_ECB)
    
    #split the string into individual words
    plaintext = plaintext.split()
    
    #for each word in the string, pad each word to a length % 16 = 0
    #by adding whitespaces
    for i in range(len(plaintext)):
        while(True):
            if(len(plaintext[i]) % 16 > 0):
                plaintext[i] += ' '
            else:
                #once the length is % 16 = 0, move on to the next word
                break

    #revert from list of words into one string
    plaintext = "".join(plaintext)

    #encode it using utf8
    msg =cipher.encrypt(plaintext.encode("utf8"))
    
    #return the encoded ciphertext
    return (msg)

def decryptAES(key, ciphertext):
    #initialise decryption using pycryptodome library
    #using AES, ECB
    decipher = AES.new(key.encode("utf8"), AES.MODE_ECB)
    
    #pass in cipherstring to be decrypted, parsing as bytes
    decryptedtext = decipher.decrypt(bytes(ciphertext))
    
    #decode decrypted text to utf8 to be human readable
    decryptedtext = decryptedtext.decode("utf8")
    
    #split string to remove padded whitespaces
    decryptedtext = decryptedtext.split()
    
    #join list of words back, adding a whitespace inbetween each element
    decryptedtext = " ".join(decryptedtext)
    
    #return decrypted text
    return (decryptedtext)

    
if __name__ == "__main__":
    app.run(debug=True)