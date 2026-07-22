#Imports
import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
import json
from collections import Counter
import csv
import os
import shutil
import re

#=====================================================================================
#CLASSES
#=====================================================================================
#Root class contains all frames
#MainRoot has all attributes of tk.Tk (allows self.__ calls from Tk)
class MainRoot(tk.Tk):
    #Initiate class code (takes variable args and keyword arguments, which will be from tk)
    def __init__(self, *args, **kwargs):
        #Made a new TK on initiation using whatever is passed to the creation of the class
        tk.Tk.__init__(self, *args, **kwargs)
        #Size to expand
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        #Style to clam theme
        appTheme = ttk.Style()
        appTheme.theme_use("clam")

        #I need the MainRoot to have access to one instance of the last session data, which means I initialize the FileData class here
        self.sessionData = FileData()

        #Name the window
        self.wm_title("OCR Review Tool")

        #Defining container to hold frames
        container = ttk.Frame(self)
        container.grid(row=0, column=0)
        container.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)

        #On initialization we want to know all frames that we can store
        #Dictionary to hold all of our frames as an attribute of self (MainRoot)
        self.frames = {}

        #Add all of our frames to the list of frames that we can access
        for frameName in (OpenPage, AuditPage): #Put frame names in parenthesis here
            #Initialize the frame classes varaibles
            frameInst = frameName(container, self)
            #Add the frame to the list
            self.frames[frameName] = frameInst
            #Define where the frame should be placed (sticky nsew means the frame will "stick" to all 4 cardinal directions)
            frameInst.grid(row=0, column=0, sticky="nsew")

        #When the program is initialized it should show the "open file" page
        self.showFrame(OpenPage)

    #=====================================================================================
    #Second method is to show a frame
    def showFrame(self, targetFrame):
        #Access the frame we want
        frame = self.frames[targetFrame]
        #Raise that frame to the top
        frame.tkraise()


#=====================================================================================
#=====================================================================================
#Make the page for opening the file
#Has access to all the properties of ttk.Frame
class OpenPage(ttk.Frame):
    #What to create when the frame is initialized
    #When initialized in MainRoot, controller is set to self(MainRoot) and parent is set to container(the frame storing all frames)
    def __init__(self, parent, controller):
        self.controller = controller
        #I want access to the data loaded in the main root for this frame
        self.sessionData = controller.sessionData

        #Text and button variables for refresh method
        self.sessionLabelText = tk.StringVar()

        #Initialize the frame
        ttk.Frame.__init__(self, parent)
        
        #Make everything stretch to fill the window
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        #Print data from last session if it exists
        #First make a label to print the data
        sessionLabel = ttk.Label(self)
        sessionLabel.config(anchor="center", justify="center", font=("", 14), textvariable=self.sessionLabelText, wraplength=500)
        #Pack the label into the grid
        sessionLabel.grid(row=0, column=0, sticky="ew")

        #We need a resume button, a restore button, an open new file, and an export last save button in row 1
        #Put them in a frame
        fileNavCont = ttk.Frame(self)
        #Resume session button (assume disabled)
        self.resumeBut = ttk.Button(fileNavCont, text="Resume", command=self.openExisting)
        self.resumeBut.state(["disabled"])
        #Restore session button (assume disabled)
        self.restoreBut = ttk.Button(fileNavCont, text="Restore Lost Session", command=self.restoreFile)
        self.restoreBut.state(["disabled"])
        #New session button (always enabled)
        newBut = ttk.Button(fileNavCont, text="Open New", command=self.openNew)
        #Export last save button (always enabled)
        exportBut = ttk.Button(fileNavCont, text="Export Review", command=self.exportReview)

        #Place the buttons into the grid
        for i, button in enumerate((self.resumeBut, self.restoreBut, newBut, exportBut)):
            button.config(width=20)
            button.grid(row=0, column=i, padx=20, pady=10, ipadx=5, ipady=5)
        #Place the frame
        fileNavCont.grid(row=1, column=0, sticky="ew")

        #Run the refresh on initialization to set buttons and text to the correct value
        self.refresh()

    #=====================================================================================
    #OPEN PAGE BUTTON METHODS
    #=====================================================================================
    #Open new file
    def openNew(self):
        #Can continue is a variable that waits for permission to open the file dialogue if there is a file in progress
        canContinue = True
        #Check if a file in progress exists
        if (not self.sessionData.finished) and (self.sessionData.lastFileName):
            #If a file does exist, set canContinue to false.
            canContinue = False
            #If one does, make a warning pop up
            fileExistsWarning = WarningPopUp(self.controller, "File already exists. Create a new file anyways?")
            fileExistsWarning.wait_window(fileExistsWarning)
            canContinue = fileExistsWarning.decision
        #Use file dialogue to get document details if we can continue
        if canContinue:
            filePath = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("Text files", "*.txt")])
            #If a file path was obtained, load the information into the session data
            if filePath:
                #Use the updateData def from the FileData class
                #All values are set to read a new file from the beginning
                self.sessionData.updateData(uFinished=False, uCurrentLine=0, uCurrentFreq=Counter({}), uCurrentErrors=[], uLastFileName = filePath)
            
                #Set the audit page display to the correct point and open it
                #Grab the audit page class from the controller
                auditPage = self.controller.frames[AuditPage]
                auditPage.refreshLine(progressRefresh = True)
                self.controller.showFrame(AuditPage)

    #=====================================================================================
    #Open existing file (the sessionData already has all of the necessary data so the audit page just needs to be loaded)
    def openExisting(self):
        #Set the audit page display to the correct point and open it
        #Grab the audit page class from the controller
        auditPage = self.controller.frames[AuditPage]
        auditPage.refreshLine(progressRefresh = True)
        self.controller.showFrame(AuditPage)

    #=====================================================================================
    #Restore file - rematches a file with the current session data, then opens the file with existing session data
    def restoreFile(self):
        filePath = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("Text files", "*.txt")])
        #If a file path was obtained, load the information into the session data
        if filePath:
            self.sessionData.updateData(uLastFileName = filePath)

        #Open file with existing data using method above
        self.openExisting()

    #=====================================================================================
    #Export review
    def exportReview(self):
        #Export CSV Errors
        errorsPath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile="errors.csv")
        if errorsPath:
            try:
                shutil.copy("data/errors.csv", errorsPath)
            except:
                with open("data/errors.csv", "w", newline="", encoding="utf-8") as file:
                    pass
                try:
                    shutil.copy("data/errors.csv", errorsPath)
                except:
                    self.sessionLabelText.set("Unexpected error occured exporting data. Restoring errors.csv path failed.")
        
        errorFreqPath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV Files", "*.csv"), ("All Files", "*.*")],
            initialfile="errorFrequency.csv")
        if errorFreqPath:
            try:
                shutil.copy("data/errorFreq.csv", errorFreqPath)
            except:
                with open("data/errorFreq.csv", "w", newline="", encoding="utf-8") as file:
                    pass
                try:
                    shutil.copy("data/errorFreq.csv", errorsPath)
                except:
                    self.sessionLabelText.set("Unexpected error occured exporting data. Restoring errorFreq.csv path failed.")

    #=====================================================================================
    #OPEN PAGE CLASS METHODS
    #=====================================================================================
    #Refresh - reloads the page with updated information
    def refresh(self):

        #Set both the variable buttons to disabled
        self.restoreBut.state(["disabled"])
        self.resumeBut.state(["disabled"])

        #We can check if the session data was found based on what sessionData.lastFileName is
        #When the name is None, the file was not found, but the data was, ask for restoring
        if self.sessionData.lastFileName is None:
            self.sessionLabelText.set("Session data was found but path is corrupt. Select restore to reopen file with current data.")
            #This should make the restore button avaiable
            self.restoreBut.state(["!disabled"])
        #When the name is none the prior session data couldn't be loaded
        elif self.sessionData.lastFileName == "":
            self.sessionLabelText.set("No session data found. Open a new file to begin program.")
        #Otherwise print the session data
        else:
            #Text for status based on if the file was marked complete or not
            status = "COMPLETED"
            #If the status is not finished, then we should make the resume button available
            if not self.sessionData.finished:
                status = "INCOMPLETE"
                self.resumeBut.state(["!disabled"])
            #If the session was not finished, 
            displayText = ("Last session data found.\nStatus:\t"+str(status)+"\nEnded on line "
                           +str(self.sessionData.currentLine)+"\Textfile name:\t"+str(self.sessionData.lastFileName))
            self.sessionLabelText.set(displayText)


#=====================================================================================
#=====================================================================================
class AuditPage(ttk.Frame):
    #Initialize with the current session statistics
    def __init__(self, parent, controller):
        #Self variables
        #Inheret session data from the controller MainRoot
        self.controller = controller
        self.sessionData = controller.sessionData
        #This is for the dynamic progress bar text
        self.progressLabelText = tk.StringVar()
        self.progressLabelText.set("")
        #This is for the dynamic last error added text
        self.lastUpdateLabelText = tk.StringVar()
        self.lastUpdateLabelText.set("")

        #Initialize the frame
        ttk.Frame.__init__(self, parent)

        #Make everything stretch to fill the window
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)

        #=========Textbox=========
        # The frame needs an element that holds the current text in a copyable form (disabled textbox)
        #Making it in its own frame to keep everything organized
        textCont = ttk.Frame(self)
        #Making the text box with disabled state
        self.currentText = tk.Text(textCont, height = 10, state="disabled", wrap="word")
        self.currentText.grid(row=0, column=0, sticky='w')
        #Adding a scrollbar
        textScroll = ttk.Scrollbar(textCont, orient=tk.VERTICAL, command=self.currentText.yview)
        #Linking the scrollbar back to the textbox
        self.currentText.config(yscrollcommand=textScroll.set)
        #Grid placement
        self.currentText.grid(row=0, column=0, sticky="ew")
        textScroll.grid(row=0, column=1, sticky="nsw")
        textCont.grid(row=0, column=0, columnspan=2, sticky="new")

        #=========Error Buttons=========
        # The frame also needs a series of buttons: missing character, extra character, incorrect character, missing text, extra text, 
        #       text misformatted, note in entry, entry in note, note misformmated, skipped line(s), other, and pass for no errors

        #Adding an embossed frame to put everything in
        buttonContStyle = ttk.Style()
        backColor = "#b4b6bb"
        buttonContStyle.configure("ButtonContStyle.TFrame", borderwidth=4, relief="sunken", padding=10, background=backColor)
        buttonCont = ttk.Frame(self, style="ButtonContStyle.TFrame")
        buttonCont.grid(row=1, column=0, sticky="w", padx=5, pady=5)
        #Styling for the buttons
        errorButStyle = ttk.Style()
        errorButStyle.configure("Error.TButton", font=("", 8), width=16, justify="left", 
                                anchor="w", borderwidth=3, bordercolor = "#77767c", relief="raised", padding=4)
        #Sytling for the labels
        errorLabelStyle = ttk.Style()
        errorLabelStyle.configure("Error.TLabel", background=backColor, font=("", 9, "bold"))

        #Character error based buttons
        characterErrorLabel = ttk.Label(buttonCont, text="Character Errors:", style="Error.TLabel")
        characterErrorLabel.grid(row=0, column=0, padx=10, pady=(15, 5), sticky="w")
        missingCharBut = ttk.Button(buttonCont, text="Missing Character", command=self.missingChar)
        extraCharBut = ttk.Button(buttonCont, text="Extra Character", command=self.extraChar)
        wrongCharBut = ttk.Button(buttonCont, text="Incorrect Character", command=self.incorrectChar)
        #Grid placing
        for i, button in enumerate((missingCharBut, extraCharBut, wrongCharBut)):
            button.config(style="Error.TButton")
            button.grid(row=i+1, column=0, padx = 5, pady = 5, sticky="w")

        #Text error based buttons
        textErrorLabel = ttk.Label(buttonCont, text="Text Level Errors:", style="Error.TLabel")
        textErrorLabel.grid(row=0, column=1, padx=10, pady=(15, 5), sticky="w")
        missingTextBut = ttk.Button(buttonCont, text="Missing Text", command=self.missingText)
        extraTextBut = ttk.Button(buttonCont, text="Extra Text", command=self.extraText)
        textMisformatedBut = ttk.Button(buttonCont, text="Misformatted Text", command=self.misformatedText)
        skippedLineBut = ttk.Button(buttonCont, text="Skipped Line(s)", command=self.skippedLine)
        #Grid placing
        for i, button in enumerate((missingTextBut, extraTextBut, textMisformatedBut, skippedLineBut)):
            button.config(style="Error.TButton")
            button.grid(row=i+1, column=1, padx = 5, pady = 5, sticky="w")

        #Note error based buttons
        notesErrorLabel = ttk.Label(buttonCont, text="Note Errors:", style="Error.TLabel")
        notesErrorLabel.grid(row=0, column=2, padx=10, pady=(15, 5), sticky="w")
        noteInEntryBut = ttk.Button(buttonCont, text="Note in Entry", command=self.noteInEntry)
        entryInNoteBut = ttk.Button(buttonCont, text="Entry in Note", command=self.entryInNote)
        noteMisformatedBut = ttk.Button(buttonCont, text="Note Misformated", command=self.noteMisformated)
        #Grid placing
        for i, button in enumerate((noteInEntryBut, entryInNoteBut, noteMisformatedBut)):
            button.config(style="Error.TButton")
            button.grid(row=i+1, column=2, padx=5, pady=5, sticky="w")

        #Other button
        otherErrorLabel = ttk.Label(buttonCont, text="Other:", style="Error.TLabel")
        otherErrorLabel.grid(row=0, column=3, padx=10, pady=(15, 5), sticky="w")
        otherBut = ttk.Button(buttonCont, text="Other", style="Error.TButton", command=self.otherError)
        otherBut.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        #Next button
        nextLabel = ttk.Label(buttonCont, text="Line Navigation", style="Error.TLabel")
        nextLabel.grid(row=3, column=3, padx=10, pady=(15, 5), sticky="w")
        nextBut = ttk.Button(buttonCont, text="Next Line", style="Error.TButton", command=self.nextLine)
        nextBut.grid(row=4, column=3, padx=5, pady=5, sticky="w")
        
        #=========Function buttons=========
        #Buttons to use the program better
        #They are going in a frame
        functionCont = ttk.Frame(self, style="ButtonContStyle.TFrame")
        #Undo button
        undoBut = ttk.Button(functionCont, text="Undo", command=self.undo)
        #Back one line button
        backLineBut = ttk.Button(functionCont, text="Go Back a Line", command=self.backLine)
        #Save button
        saveBut = ttk.Button(functionCont, text="Save", command=self.completeAudit)
        #End review button
        endBut = ttk.Button(functionCont, text="End Review Early", command=self.endEarly)
        #Grid placement
        for i, button in enumerate((undoBut, backLineBut, saveBut, endBut)):
            button.config(style="Error.TButton")
            button.grid(column=0, row=i, padx = 5, pady = 5, sticky="ew")
        functionCont.grid(row=1, column=1, sticky="nsw", padx=5, pady=5)


        #=========Add a progress bar to the bottom of the page=========
        #This is going in another frame
        progressCont = ttk.Frame(self)
        progressCont.rowconfigure(0, weight=1)
        progressCont.columnconfigure(0, weight=1)
        #Error update displays the last error added and at what line in the original file
        lastErrorLabel = ttk.Label(progressCont, textvariable=self.lastUpdateLabelText, anchor="center")
        #Progress label shows how many entries are done and how many remain
        progressLabel = ttk.Label(progressCont, textvariable=self.progressLabelText, anchor="center")
        #Progress is a progressbar beneath it for visual aid
        self.progress = ttk.Progressbar(progressCont, value=self.sessionData.currentLine, maximum=len(self.sessionData.allText))
        #Grid configuration
        lastErrorLabel.grid(row=0, column=0, padx=5, pady=(5, 3), sticky="ew")
        progressLabel.grid(row=1, column=0, padx=5, pady=(0, 3), sticky="ew")
        self.progress.grid(row=2, column=0, padx=5, pady=(2,5), sticky="ew")
        progressCont.grid(row=3, column=0, columnspan=2, sticky="ew")


    #=====================================================================================
    #BUTTON FUNCTIONS
    #=====================================================================================
    #End early - end the review before finishing the entire file
    def endEarly(self):
        #Make a warning prompt
        endEarlyWarning = WarningPopUp(self.controller, "Are you sure you want to end the review early? This will finalize all CSV files for export.")
        #Wait for a response
        endEarlyWarning.wait_window(endEarlyWarning)
        #Get the user's decision
        decision = endEarlyWarning.decision
        #If the user selected yes, run complete audit
        if decision:
            self.completeAudit(end=True)

    #Undo - remove the last error from the 2 lists in session data
    def undo(self):
        #Try to get the last error from the session data
        try:
            lastError = self.sessionData.currentErrors[-1][1]
        #Exception for if the index is out of range (indicates empty chart)
        except IndexError:
            #Change the update label to communicate the error
            self.lastUpdateLabelText.set("No errors to undo")
            #Escape the method
            return

        #Remove the last index from session data current errors
        self.sessionData.currentErrors.pop()
        #Count down one for errorFreq using last error as the key
        #Flatten error for the counter
        flatError = str(lastError[0])+", "+str(lastError[1])
        self.sessionData.currentFreq[flatError] -= 1
        #Set the update text to communicate success
        self.lastUpdateLabelText.set("Removed error "+str(lastError)+" from data")
            

    #=====================================================================================
    #Next line - update the current line and display
    def nextLine(self):
        #Update the current line (stored in sessionData)
        self.sessionData.currentLine += 1
        #If we've reached the end of the file, complete audit
        if self.sessionData.currentLine >= len(self.sessionData.allText):
            self.completeAudit(end=True)
        #Otherwise update the page
        else:
            #Use refresh line
            self.refreshLine()
            #Increase the progress bar by one
            self.progress.step()

    #=====================================================================================
    #Back line - update the current line to go back one and display
    def backLine(self):
        #Update the current line (stored in sessionData)
        self.sessionData.currentLine -= 1
        #Make sure that the current line is at least 0
        #If the current line is less than 0, set it to 0 and update the last update text to explain the error
        if self.sessionData.currentLine < 0:
            self.sessionData.currentLine = 0
            self.lastUpdateLabelText.set("Can't go back anymore (beginning of file)")
        #Otherwise run all the updates
        else:
            #Use refresh line
            self.refreshLine()
            #Put the progress bar back one step
            self.progress.step(-1)

    #=====================================================================================
    #Missing character button
    def missingChar(self):
        #Make an error entry pop up with no correction
        self.displayErrorPop("Missing Character", False)

    #=====================================================================================
    #Extra character button
    def extraChar(self):
        #Make an error entry pop up with no correction
        self.displayErrorPop("Extra Character", False)

    #=====================================================================================
    #Incorrect character button
    def incorrectChar(self):
        #Make and error entry pop up with correction
        self.displayErrorPop("Incorrect Character", True)
    
    #=====================================================================================
    #Missing text button
    def missingText(self):
        #Make an error entry pop up with no correction
        self.displayErrorPop("Missing Text", True)

    #=====================================================================================
    #Extra text button
    def extraText(self):
        #Make an error entry pop up with no correction
        self.displayErrorPop("Extra Text", False)
    
    #=====================================================================================
    #Misformated text button
    def misformatedText(self):
        #Add an error for misformatting
        self.appendError(("Misformated Text", "N/A"))

    #=====================================================================================
    def skippedLine(self):
        #Add an error for skipped lines
        self.appendError(("Skipped Line(s)", "N/A"))

    #=====================================================================================
    #Note in entry button
    def noteInEntry(self):
        #Make an error entry pop up with no correction
        self.displayErrorPop("Note in Entry", False)

    #=====================================================================================
    #Entry in note button
    def entryInNote(self):
        #Make an error entry pop up with no correction
        self.displayErrorPop("Entry in Note", False)

    #=====================================================================================
    #Note misformatted button
    def noteMisformated(self):
        #Add an error for misformatting
        self.appendError(("Misformated Note", "N/A"))

    #=====================================================================================
    #Other button
    def otherError(self):
        #Make an error entry pop up with correction
        self.displayErrorPop("Other Error", True)


    #=====================================================================================
    #Submit error button - used in display error frame to get the error from the submission
    #Adds the error to the session data lists
    #Finally, closes the error popup
    def submitError(self, errorPop, errorText, correctionText=None):
        #Create a new error entry
        newError = (errorText, "N/A")
        #If there is correction text, update the error tuple to reflect it
        if correctionText:
            newError = (errorText, correctionText)
        #Add the error 
        self.appendError(newError)

        #Close the popup
        errorPop.destroy()


    #=====================================================================================
    #AUDIT PAGE CLASS FUNCTIONS
    #=====================================================================================
    #Append error method (will be used in most button methods)
    #Error is a tuple in form (error, correction)
    #Correction may be N/A in cases
    def appendError(self, error):
        #Flatten error for the counter
        flatError = str(error[0])+", "+str(error[1])
        #Add the error to the current error freq counter
        self.sessionData.currentFreq[flatError] += 1
        #Add the XML line number and error to the current errors list
        self.sessionData.currentErrors.append((self.sessionData.allText[self.sessionData.currentLine], error))
        #Update the dynamic text that shows the last added error
        #String variable for readability
        lastAdded = "Last error added: "+str(error)+" found at original text line "+str(self.sessionData.allText[self.sessionData.currentLine][0])
        self.lastUpdateLabelText.set(lastAdded)
     
    #=====================================================================================
    #Display error frame - enable and display the error popup with a variable label and the correction field enabled/disabled
    def displayErrorPop(self, errorLabel, hasCorrection):
        #Make a popup
        errorPop = tk.Toplevel(self.controller)
        errorPop.wm_title("Enter Error Data")
        #Force interaction
        errorPop.grab_set()
        errorEntryCont = ttk.Frame(errorPop)
        errorContLabel = ttk.Label(errorEntryCont, text="Enter error information below:")
        #Error entry
        errorFieldLabel = ttk.Label(errorEntryCont, text=str(errorLabel)+": ")
        errorFieldEntry = ttk.Entry(errorEntryCont, width=40)
        #Correction field
        correctionFieldLabel = ttk.Label(errorEntryCont, text="Correction (if applicable): ")
        correctionFieldEntry = ttk.Entry(errorEntryCont, width=40)
        #Submit button
        submitErrorBut = ttk.Button(errorEntryCont, text="Submit", width=20, 
                                    command=lambda: self.submitError(errorPop, str(errorLabel)+": "+str(errorFieldEntry.get()), 
                                                                     correctionFieldEntry.get()))
        
        #If there is not a correction to be made, set the correction field to disabled 
        #   and configure the submit error button to have no correction field defined
        if not hasCorrection:
            correctionFieldEntry.config(state="disabled")
            submitErrorBut.config(command=lambda: self.submitError(errorPop, str(errorLabel)+": "+str(errorFieldEntry.get())))

        #Place everything in the grid
        errorContLabel.grid(row=0, column=0, pady=(0, 10), sticky="w")
        errorFieldLabel.grid(row=1, column=0, pady=5, sticky="w")
        errorFieldEntry.grid(row=2, column=0, pady=(0, 5), sticky="w")
        correctionFieldLabel.grid(row=3, column=0, pady=5, sticky="w")
        correctionFieldEntry.grid(row=4, column=0, pady=(0, 5), sticky="w")
        submitErrorBut.grid(row=5, column=0, pady=5, sticky="e")
        #Place the frame in the window
        errorEntryCont.grid(row=0, column=0, padx=5)
        errorPop.wait_window()


    #=====================================================================================
    #refreshLine - open the text to the session data current line and fix the progressbar
    #progressRefresh is so that when loading a file, the progress bar current value and max value are set properly
    def refreshLine(self, progressRefresh = False):
        #Replacing current text
        #The text box has to be temporarily enabled to do this
        self.currentText.config(state="normal")
        self.currentText.delete("1.0", tk.END)
        #Formatting the text over a few variables for readability
        #The text is in session data allText[currentLine][1][2][3] ([0] is the XML line number)
        line = self.sessionData.currentLine
        currentTextFormat = ("TEXT: "+str(self.sessionData.allText[line][1])+"\nKIND OF TEXT = "+str(self.sessionData.allText[line][2])+
                             "\nSOURCE NOTES: "+self.sessionData.allText[line][3])
        self.currentText.insert("1.0", currentTextFormat)
        #Re-disable the text
        self.currentText.config(state="disabled")

        #Set the progress bar text to the format "currentLine #/allLines #" (index 0 is line 1 in human counting, so add 1)
        self.progressLabelText.set(str(line+1)+"/"+str(len(self.sessionData.allText)))

        #If the progress bar needs to be refreshed, do that
        if progressRefresh:
            self.progress.config(maximum=len(self.sessionData.allText), value=self.sessionData.currentLine)
    
    #=====================================================================================
    #End audit - if we reach the last line or quit, do all the things to complete the audit
    def completeAudit(self, end=False):
        #If this is the end of the audit, set session data's finished variable to true and update the CSVs
        if end:
            self.lastUpdateLabelText.set("Text completed, updating files for export...")
            self.controller.after(2000)
            self.sessionData.finished = True
            self.sessionData.updateCSV()
            
        #Run session data's update method
        self.sessionData.finishSessionUpdate()

        #Open home page again
        #We also need to access the home page's object and update the buttons
        #Grab the open page instance from the controller and run its refresh method
        openPage = self.controller.frames[OpenPage]
        openPage.refresh()
        #Show the frame
        self.controller.showFrame(OpenPage)


#=====================================================================================
#=====================================================================================
#Warning pop up
class WarningPopUp(tk.Toplevel):
    def __init__(self, controller, displaytext):
        #Create a variable to track a decision (yes/no in nature)
        self.decision = None
        #Make the pop up
        #Root window
        tk.Toplevel.__init__(self, controller)
        self.wm_title("Warning")
        #Force user interaction on this popup
        self.grab_set()
        #Elements in the window
        #The warning label is whatever text was passed to the init method when called
        warningLabel = ttk.Label(self, text=displaytext)
        yesBut = ttk.Button(self, text="Yes", width=20, command=self.yesPress)
        noBut = ttk.Button(self, text="No", width=20, command=self.noPress)
        #Placing elements
        warningLabel.grid(row=0, column=0, columnspan=2, sticky="ew")
        yesBut.grid(row=1, column=1, sticky="e")
        noBut.grid(row=1, column=0, sticky="e")

    #=====================================================================================
    #Button commands
    # Updates the value of decision based on which button was pressed, and then destroys the window
    #The class object stores a decision in self.decision as None (window closed/no option selected), True (yes), or False(no)
    #Yes button pressed
    def yesPress(self):
        self.decision = True
        self.destroy()
    #No button pressed
    def noPress(self):
        self.decision = False
        self.destroy()

#=====================================================================================
#=====================================================================================
#Class for storing and accessing output files and its data
class FileData:
    #Initialize with the data folders contents stored
    def __init__(self, errorFreq="data/errorFreq.csv", errors="data/errors.csv", allTextCSV = "data/allText.csv", last="data/lastsession.json"):
        self.errorFreq = errorFreq
        self.errors = errors
        self.allTextCSV = allTextCSV
        self.last = last

        #Read the last session file to get extra data during intialization
        with open(self.last, 'r', encoding="utf-8") as file:
            try:
                #Initialize all data into a json
                self.sessionData = json.load(file)
            except Exception:
                self.sessionData = {}

        #Grab the variables out of the dictionary
        #Variables are finished, currentLine (current index in allText), allText, currentFreq, currentErrors, lastFileName
        #Using a try catch in case data doesn't exist
        try:
            self.finished = bool(self.sessionData["finished"])
            self.currentLine = int(self.sessionData["currentLine"])
            self.allText = list(self.sessionData["allText"])
            self.currentFreq = Counter(dict(self.sessionData["currentFreq"]))
            self.currentErrors = list(self.sessionData["currentErrors"])
            self.lastFileName = str(self.sessionData["lastFileName"])
        #If data is missing, reinitialize the data at 0/empty
        except Exception:
            self.finished = False
            self.currentLine = 0
            self.allText = []
            self.currentFreq = Counter({})
            self.currentErrors = []
            self.lastFileName = ""

        #Also assert that the last file name even exists
        #If there's no a name but no file, we'll set last file name to none
        if self.lastFileName != "":
            try:
                assert os.path.isfile(self.lastFileName)
            #If the file name doesn't exist, set the last file name to none
            #We'll check this later to let the user open a file if it was accidentally renamed or something
            except AssertionError:
                self.lastFileName = None


    #=====================================================================================
    #SESSION DATA CLASS FUNCTIONS
    #=====================================================================================
    #Open text - open a new XML file and process it into a text file
    def openText(self):
        #Make sure the all text variable is empty
        self.allText = []
        #Regex capturing 
        # "bad starts" are for lines that don't have form or transl data
        badStart = r"<\/?(M|W|S|(TEXT)|\?)"
        #For extracting notes
        notesMark = r"notes=\"(.*?)\""
        #For extracting "kindOf"
        kindOfMark = r"kindOf=\"(.*?)\""
        #For extracting the text from between the ><
        dataMark = r"\>(.*?)\<"

        with open(self.lastFileName, "r", encoding="utf-8") as file:
            #Go through each line
            for i, line in enumerate(file):
                #Only proceed if the line has information and doesn't match bad start
                if not re.search(badStart, line) and line:

                    #Getting notes and kindOf data
                    #Initialize notes and kindOf data
                    notes=""
                    kindOf =""
                    data = ""
                    #Look for the kindOf, notes, and data
                    notesMatch = re.search(notesMark, line)
                    kindOfMatch = re.search(kindOfMark, line)
                    dataMatch = re.search(dataMark, line)
                    #If a match was found, reassign notes/kindOf/data to the match
                    #Also cut off the extra formatting characters in the pattern
                    if notesMatch:
                        notes = notesMatch.group()[7:-1]
                    if kindOfMatch:
                        kindOf = kindOfMatch.group()[8:-1]
                    if dataMatch:
                        data = dataMatch.group()[1:-1]
                    
                    #Make the row entry by appending a tuple
                    #Order is lineNo, text, kind of, and then notes
                    #Line number is index + 1 since rows start at 0 in python
                    self.allText.append((i+1, data, kindOf, notes))
                

    #=====================================================================================
    #Update data
    #Update any new data passed to this def to the class object
    #Self variables that can be updated are finished, currentLine, currentFreq, currentErrors, lastFileName
    #This method also handles opening the data file if it was updated
    def updateData(self, uFinished=None, uCurrentLine=None, uCurrentFreq=None, uCurrentErrors=None, uLastFileName = None):
        #Make 2 lists to iterate through that matches passed variables to the self values
        updateValues = [uFinished, uCurrentLine, uCurrentFreq, uCurrentErrors, uLastFileName]
        selfValues = ["finished", "currentLine", "currentFreq", "currentErrors", "lastFileName"]
        #Iterate through the 2 lists
        for update, current in zip(updateValues, selfValues):
            #Only update a value if it was assigned one when the method was called
            if update != None:
                setattr(self, current, update)
        
        #If an updated file name was given, open the allText variable to the new text file
        if uLastFileName != None:
            self.openText()
    
    #=====================================================================================
    #Finish Session Update
    # When the application is done, set the values in the dictionary sessionData and write the dict to the json
    def finishSessionUpdate(self):
        #Update the dictionary of session data
        self.sessionData["finished"] = self.finished
        self.sessionData["currentLine"] = self.currentLine
        self.sessionData["allText"] = self.allText
        #Counter object must be saved as dictionary
        self.sessionData["currentFreq"] = dict(self.currentFreq)
        self.sessionData["currentErrors"] = self.currentErrors
        self.sessionData["lastFileName"] = self.lastFileName

        #Open the json and dump the file
        with open(self.last, 'w', encoding="utf-8") as file:
            #Initialize all data into a json
            json.dump(self.sessionData, file)

    #=====================================================================================
    #Update CSV
    # When the file has been fully processed, update the CSV files
    def updateCSV(self):
        #Update the currentText csv so that it contains the currentText
        with open(self.allTextCSV, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerows(self.allText)
        
        #Update the errors csv
        with open(self.errors, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            #Header
            writer.writerow(["Line in XML", "Error"])
            #Data
            writer.writerows(self.currentErrors)

        #Update the errorFreq csv
        #This one needs a bit of adaptation to go from a counter to a CSV
        errorFreqList = []
        #Go through each entry in the Counter and flatten it to a tuple
        for entry in self.currentFreq:
                errorFreqList.append((entry, self.currentFreq[entry]))
        #Use CSV writer to write the list of tuples to the file
        with open(self.errorFreq, "w", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            #Header
            writer.writerow(["Error and Correction", "Occurances"])
            #Data
            writer.writerows(errorFreqList)
            
    
#=====================================================================================

def main():
    app = MainRoot()
    app.mainloop()

if __name__ == "__main__":
    main()