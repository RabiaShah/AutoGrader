from flask import Flask,render_template,request,redirect, url_for
import spacy
import en_core_web_sm
from spacy.lang.en.stop_words import STOP_WORDS
from pymongo import MongoClient

app=Flask("__main__")
app.debug=True
# nlp = spacy.load('en_core_web_sm')
nlp=en_core_web_sm.load()
client=MongoClient('mongodb://localhost:27017')

Total_Marks=""
Question=""

ExamDoc=[]
AnsDoc=[]
Title=""
count=0
collectionName=''
stdColName=''
StudentName='Student'
InstructorName='Instructor'


class Exam:
    Question=""
    Solution=""
    Total_Marks=""
    count=0

    def __init__(self,question,solution,total_marks):
        self.Question=question
        self.Solution=solution
        self.Total_Marks=total_marks
        Exam.count+=1

    def print(self):
        string=self.Question+"  "+self.Solution+"   "+self.Total_Marks+"    "
        return string

class Database:
    
    db=client.Autograder
    collection=db.newcollection
    AllCollections=db.list_collection_names()
    
    
    FindName="quiz"+str(len(AllCollections))
    global StudentName
    stdDB=client[StudentName]

    def createExam(self,instName,question,solution,marks,title):
        allCollections=self.db.list_collection_names()
        CreateName="quiz"+str(len(allCollections)+1)
        instDb=client[instName]
        instCollection=instDb[CreateName]
        newCollection=self.db[CreateName]
        doc={"Question":question,
        "Solution":solution,
        "Marks":marks,
        "Title":title
        }
        addDoc=newCollection.insert_one(doc) 
        instCollection.insert_one(doc)
        return addDoc
    
    def updateCollectionNum(self):
        documents=self.collection.find({},{'collections':1,'_id':0}) #for reading whatever value is stored in the collections column/field
        for doc in documents:
            collecNum=doc['collections']
        if int(collecNum)<len(self.AllCollections):
            self.collection.update_one({
                'collections':collecNum
            },
            {
                '$set':{
                    'collections':str(len(self.AllCollections))
                }
            })
            newQuiz=True
        else:
            newQuiz=False

        return str(newQuiz)

    def AttemptExam(self,dbname,stdColName):

        exam=self.db[stdColName]
        examList=exam.find()
        
        global AnsDoc
        global Title
        
        for exams in examList:
            print(exams['Question'])
            print(exams['Marks'])
            AnsDoc.append(Exam(exams['Question'],"",exams['Marks']))
            Title=exams['Title']
            print(exams['Title'])
        
        return AnsDoc

    def StudentDatabase(self,stdName):
        collecList=self.db.list_collection_names()
        collecList.remove('newcollection')
        collecList.sort()
        stdDB=client[stdName]
        stdCollecList=stdDB.list_collection_names()
        for collec in collecList:
            if collec not in stdCollecList:
                newcol=stdDB[collec]
                tempdata=self.db[collec].find()
                for data in tempdata:
                    doc={
                        "Question":data['Question'],
                        "Marks":data['Marks'],
                        "Title":data['Title'],
                    }
                    result=newcol.insert_one(doc)
        
        return result
    
    def StudentNewExam(self,dbName):
        ExamCollecList=self.db.list_collection_names()
        ExamCollecList.remove('newcollection')
        stdDB=client[dbName]
        StdCollecList=stdDB.list_collection_names()

        new=[]
        titleList=[]
        for collec in ExamCollecList:
            if collec not in StdCollecList:
                collection=self.db[collec]  
                doc=collection.find_one()    #find that collection in the database and find any one of it's document (question)
                title=doc['Title']           #save that document's title and append it into the list, then return both the lists.
                titleList.append(title)
                new.append(collec)

        return new, titleList

    
    def getCollectionNames(self):
        result=self.db.list_collection_names()
        result.remove('newcollection')
        result.sort(reverse=True)
        titleCol=[]
        for name in result:
            collection=self.db[name]
            doc=collection.find_one()
            title=doc['Title']
            titleCol.append(title)
        return result,titleCol
    
    def getExamData(self,dbname):
        collection=self.db[dbname]
        data=collection.find({})
        mylist=[]
        for d in data:
            mylist.append(d)
        return mylist
    
    def StudentAnswer(self,dbname,question,answer,title):
        collection=self.stdDB[dbname]
        doc={
            "Question":question,
            "Answer":answer,
            "Title":title,
            "Exam":dbname
        }
        result=collection.insert_one(doc)
        return result
    
    def AddAnswer(self,dbname,colname,question,answer,marks,title,result):
        db=client[dbname]
        coll=db[colname]
        mark=int(int(marks)*result)
        doc={
            "Question":question,
            "Answer":answer,
            "Marks":marks,
            "Title":title,
            "Percentage":result,
            "Obtained_Marks":mark
        }
        result=coll.insert_one(doc)
        return result
    
    def getCollectionsandTitles(self, dbname):
        stdDB=client[dbname.strip()]
        result=stdDB.list_collection_names()
        titleCol=[]
        for name in result:
            collection=stdDB[name]
            doc=collection.find_one()
            title=doc['Title']
            titleCol.append(title)
        return result,titleCol
    
    
    def Login(self,username,password):
        infoDB=client.Info
        collections=infoDB.login
        documents=collections.find()
        found=False
        for doc in documents:
            if doc['username']==username:
                
                if doc['password']==password:
                    
                    found=True
                    break
                else:
                    
                    found=False
                    break
            else:
                found=False
                
        
        return found
    
    def getRole(self,username):
        infoDB=client.Info
        collection=infoDB.login
        documents=collection.find()
        for doc in documents:
            if doc['username']==username:
                role=doc['role']
        
        return role
    
    def getStudents(self):
        infoDB=client.Info
        collections=infoDB.login
        documents=collections.find()
        Students=[]
        for doc in documents:
            if doc['role']=='student':
                Students.append(doc['username'])
        
        return Students


class Grading:

    def getSolution(self,collName):
        db=client.Autograder
        collection=db[collName.strip()]
        documents=collection.find()
        SolDoc=[]
        for doc in documents:
            SolDoc.append(doc['Solution'])

        return SolDoc
    
    def getAnswers(self,dbname,collName):
        db=client[dbname.strip()]
        collection=db[collName]
        documents=collection.find()
        AnswerDoc=[]
        for doc in documents:
            AnswerDoc.append(doc['Answer'])
        
        return AnswerDoc
    
    def getMarks(self,collName):
        db=client.Autograder
        collection=db[collName.strip()]
        documents=collection.find()
        MarkDoc=[]
        for doc in documents:
            MarkDoc.append(doc['Marks'])

        return MarkDoc
    
    def getQuestion(self,collName):
        db=client.Autograder
        collection=db[collName.strip()]
        documents=collection.find()
        global Title
        QuesDoc=[]
        for doc in documents:
            QuesDoc.append(doc['Question'])
            Title=doc['Title']

        return QuesDoc
    
    def Grade(self,Solution,Answer):
        strSol=Solution.split()
        strAns=Answer.split()

        cleanSol=[word for word in strSol if word not in STOP_WORDS]
        cleanAns=[word for word in strAns if word not in STOP_WORDS]

        sol=""
        for word in cleanSol:
            sol+=word
            sol+=" "
        
        ans=""
        for word in cleanAns:
            ans+=word
            ans+=" "

        solution=nlp(sol)
        answer=nlp(ans)

        result=solution.similarity(answer)

        return result

class Result:

    def getGrade(self,dbname,collectionName, ans):
        obj=Grading()
        QuesDoc=obj.getQuestion(collectionName)
        SolDoc=obj.getSolution(collectionName)
        # AnsDoc=obj.getAnswers(dbname,collectionName)
        MarksDoc=obj.getMarks(collectionName)
        count=0
        ResultDoc=[]
        for sol in SolDoc:
            marks=float(MarksDoc[count])
            grade=int(obj.Grade(sol,ans))
            print(grade)
            result=int(marks*grade)
            print(result)
            ResultDoc.append(result)

            #storing in the student's database in the same collection where the questions and answers are stored
            stdDB=client[dbname.strip()]
            collection=stdDB[collectionName.strip()]
            doc=collection.update({
                "Question":QuesDoc[count]
            },
            {
                "$set":
                {
                    "Obtained_Marks":str(result),
                    "Percentage":str(grade)
                }
            })
            count+=1
            print(doc)
        
        
        return ResultDoc

    def DisplayResult(self,dbname,collectionName):
        stdDB=client[dbname]
        collection=stdDB[collectionName]
        document=collection.find({"Percentage":{"$exists":True}})
        tempList=[]
        if document!=None:
            for doc in document:
                tempDict={}
                tempDict['Question']=doc['Question']
                tempDict['Answer']=doc['Answer']
                tempDict['Obtained_Marks']=doc['Obtained_Marks']
                tempDict['Total_Marks']=doc['Marks']
                tempDict['Percentage']=doc['Percentage']
                tempList.append(tempDict)
                
        
        return tempList












        
        

    
    



@app.route('/')
def main():
    return redirect(url_for('login'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/login',methods=["GET","POST"])
def loginPost():
    username=request.form["username"]
    password=request.form["password"]
    print(username+"  "+password)
    objDB=Database()
    result=objDB.Login(username,password)
    if result==True:
        role=objDB.getRole(username)
        if role=="instructor":
            global InstructorName
            InstructorName=username.strip()
            return redirect(url_for('instructor_dashboard'))
        if role=="student":
            global StudentName
            StudentName=username.strip()
            return redirect(url_for('student_dashboard'))
        
    else:
        errorMsg="* Invalid Username and Password Combination"
        return render_template('login.html',error=errorMsg)
    
    return render_template('login.html')

@app.route('/view-questions')
def view_questions():
    return render_template('view-questions.html')

@app.route('/view-questions',methods=["GET","POST"])
def view_question():
    return render_template('view-questions.html')




@app.route('/instructor-dashboard')
def instructor_dashboard():
    return render_template('instructor-dashboard.html')

@app.route('/instructor-dashboard', methods=["GET","POST"])
def instructor_dashboards():
    btnClick=request.form["open"]
    if btnClick=="view":
        return redirect(url_for('instructor_exams'))
    
    if btnClick=="add":
        return redirect(url_for('instructor'))
    
    if btnClick=="result":
        return redirect(url_for('instructor_results'))





@app.route('/student-dashboard')
def student_dashboard():
    global StudentName
    return render_template('student-dashboard.html',name=StudentName)

@app.route('/student-dashboard',methods=["GET","POST"])
def student_dashboards():
    btnClick=request.form["open"]
    if btnClick=="exam":
        return redirect(url_for('student_exams'))
    else:
        return redirect(url_for('student_results'))

@app.route('/student-results')
def student_results():
    global StudentName
    obj=Database()
    names,titles=obj.getCollectionsandTitles(StudentName)
    mylist=zip(names,titles)
    return render_template('student-results.html',name=StudentName,listi=mylist)

@app.route('/student-results',methods=["GET","POST"])
def student_result():
    global stdColName
    collec=request.form["open"]
    stdColName=collec.strip()
    return redirect(url_for('resultSTD'))

@app.route('/Student-Result')
def resultSTD():
    obj=Result()
    global stdColName
    print(stdColName)
    global StudentName
    print(StudentName)
    result=obj.DisplayResult(StudentName,stdColName.strip())
    marks=0.0
    total=0
    for doc in result:
        print(doc['Obtained_Marks'])
        marks+=int(doc['Obtained_Marks'])
        total+=int(doc['Total_Marks'])
    
    percentage=(marks/total)*100

    return render_template('resultSTD.html',documents=result,marks=marks,total=total,percentage=percentage)


@app.route('/result')
def result():
    obj=Result()
    global stdColName
    print(stdColName)
    global StudentName
    print(StudentName)
    result=obj.DisplayResult(StudentName,stdColName.strip())
    marks=0.0
    total=0
    for doc in result:
        print(doc['Obtained_Marks'])
        marks+=int(doc['Obtained_Marks'])
        total+=int(doc['Total_Marks'])
    
    percentage=(marks/total)*100

    return render_template('result.html',documents=result,marks=marks,total=total,percentage=percentage)

@app.route('/student-exams')
def student_exams():
    obj=Database()
    global StudentName

    names,titles=obj.StudentNewExam(StudentName)
    newList=zip(names,titles)
    return render_template('student-exams.html',name=StudentName ,listi=newList)

@app.route('/student-exams',methods=["GET","POST"])
def student_exam():
    global stdColName
    name=request.form["open"]
    print(name)
    stdColName=name.strip()
    obj=Database()
    global StudentName
    print(str(obj.AttemptExam(StudentName,stdColName)))
    return redirect(url_for('quiz'))

@app.route('/instructor')
def instructor():
    global Title
    return render_template('instructor.html',titleValue=Title)

@app.route('/instructor',methods=["GET","POST"])
def instruct():
    dbObj=Database()
    global Title
    Title=request.form["title"]
    Question=request.form["quest"]
    Solution=request.form["solution"]
    Total_Marks=request.form["marks"]
    global ExamDoc
    global InstructorName
    btnRequest=request.form["button"]
    if btnRequest=="save":
        
        ExamDoc.append(Exam(Question,Solution,Total_Marks))
        print(len(ExamDoc))
        for doc in ExamDoc:
            dbObj.createExam(InstructorName,doc.Question,doc.Solution,doc.Total_Marks,Title)
        ExamDoc.clear()
        Title=""
        return redirect(url_for('instructor_dashboard'))
    else:
        ExamDoc.append(Exam(Question,Solution,Total_Marks))
        return redirect(url_for('instructor'))
        

@app.route('/', methods=["GET","POST"])
def newmain():
    global Question
    Question=request.form["quest"]
    print(Question)
    global Solution
    Solution=request.form["solution"]
    print(Solution)
    Save=request.form["button"]
    # Next=request.form["next"]
    print(Save)
    return redirect(url_for('add_marks'))

@app.route('/quiz')
def quiz():
    global count
    global AnsDoc
    global stdColName
    global StudentName
    # print(len(AnsDoc))
    # doc=AnsDoc[count]
    obj=Grading()
    questions=obj.getQuestion(stdColName)
    
    marks=obj.getMarks(stdColName)
    
    return render_template('quiz.html',name=StudentName ,ques=questions[count],num=str(count+1),marks=marks[count],total=str(len(AnsDoc)))



@app.route('/quiz',methods=["GET","POST"])
def funct():
    global count
    global AnsDoc
    global stdColName
    global StudentName
    global Title
    objGrading=Grading()
    solutions=objGrading.getSolution(stdColName)
    questions=objGrading.getQuestion(stdColName)
    marks=objGrading.getMarks(stdColName)
    print(count)
    Answer=request.form["answer"]
    print(Answer)
    obj=Database()
    btnPress=request.form["button"]
    if btnPress=="next":
        # doc=AnsDoc[count]
        
        # objResult=Result()
        objGrade=Grading()
        # objResult.getGrade(StudentName,stdColName,Answer)
        result=objGrade.Grade(solutions[count],Answer)
        obj.AddAnswer(StudentName,stdColName,questions[count],Answer,marks[count],Title,result)
        print(result)
        if count==(len(questions)-1):
            AnsDoc.clear()
            return redirect(url_for('resultSTD'))
        else:
            count=count+1
            return redirect(url_for('quiz'))
    else:
        objResult=Result()
        objGrade=Grading()
        
        objResult.getGrade(StudentName,stdColName,Answer)
        result=objGrade.Grade(solutions[count],Answer)
        obj.AddAnswer(StudentName,stdColName,questions[count],Answer,marks[count],Title,result)
        print(result)
        return redirect(url_for('resultSTD'))






    # print(Answer)
    # return "<h1>Successfully Added</h1>"

# @app.route('/add_marks')
# def add_mark():
#     return render_template('add-marks.html')

# @app.route('/add_marks',methods=["GET","POST"])
# def get_marks():
#     global Total_Marks
#     Total_Marks=request.form["marks"]
#     print(Total_Marks)
#     global Question
#     return redirect(url_for('quizfunc'))



@app.route('/instructor-results')
def instructor_results():
    objDB=Database()
    Students=objDB.getStudents()
    for std in Students:
        print(std)
    return render_template('instructor-results.html',Student=Students)

@app.route('/instructor-results', methods=["GET","POST"])
def instructor_result():
    btn=request.form["open"]
    global StudentName
    StudentName=btn.strip()
    return redirect(url_for('alls'))

@app.route('/instructor-allresults')
def alls():
    obj=Database()
    names,titles=obj.getCollectionsandTitles(StudentName)
    mylist=zip(names,titles)
    return render_template('instructor-allresults.html',mylist=mylist)

@app.route('/instructor-allresults', methods=["GET","POST"])
def allss():
    global stdColName
    Name=request.form["open"]
    stdColName=Name.strip()
    return redirect(url_for('result'))


@app.route('/instructor-exams')
def instructor_exams():
    obj=Database()
    names,titles=obj.getCollectionNames()
    mylist=zip(names,titles)
    return render_template('instructor-exams.html',listi=mylist)

@app.route('/instructor-exams',methods=["GET","POST"])
def examsfunc():
    global collectionName
    collectionName=request.form["open"]
    return redirect(url_for('exam_questions'))

@app.route('/exam-questions')
def exam_questions():
    global collectionName
    obj=Database()
    data=obj.getExamData(collectionName.strip())
    titles=data[0]['Title']
    return render_template('exam-questions.html',title=titles,documents=data)



app.run()