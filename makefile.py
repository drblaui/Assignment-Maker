import os, re, json, shutil

class Makefile:
	def __init__(self):
		self.informations = {}
		#Read Settings
		if(self.settings_exist()):
			with open("makefile_settings.json", 'r', encoding="UTF-8") as jsonfile:
				# Exclude comments (saves space)
				jsondata = ''.join(line for line in jsonfile if not ("_comment" in line))
				self.informations = json.loads(jsondata)	
			
			if(self.informations["auto_increment"]):
				lastnumber = self.get_last_assignment()
				if lastnumber == False:
					print("Konnte letztes Assignment nicht finden, bitte Blattnummer eingeben")
					self.write_settings("assignment_number", "Arbeitsblatt Nummer:\n")
				else:
					self.assignment_number = (lastnumber + int(self.informations["auto_increment_steps"]))
		else:
			sets= {
				"lecturer_name": "Name des Dozenten/der Dozentin:\n",
				"tutor_name": "Name des Tutors/der Tutorin:\n",
				"tutorial_number": "Nummer des Tutoriums: \n",
				"lecture_name": "Name der Veranstaltung: \n",
				"semester_id": "Semester:\n",
				"student_names": "Name der Student*Innen (Personen mit Komma trennen):\n",
				"output_folder": "Output Ordner: \nLeer lassen, wenn Standard Ordner benutzt werden soll\n",
				"output_filename": "Output Dateiname: \n Leer lassen, wenn Standard benutzt werden soll\n",
				"save_settings": "Diese Einstellungen für später speichern (y/n)\n(Generiert eine makefile_settings.json Datei)\n",
				"assignment_number": "Arbeitsblatt Nummer:\n",
				"auto_increment": "Diese Nummer automatisch hochzählen (y/n): \n(Benötigt zustimmung zum speichern von Einstellungen)\n",
				"auto_increment_steps": "Anzahl an Schritte zum hochzählen:\n(1 = 1,2,3,...; 2 = 2,4,6,...)\n"
			}

			for question in sets:
				y_n = False
				if question == "auto_increment_steps" and not self.informations["auto_increment"]:
					continue
				if question == "auto_increment" or question == "save_settings":
					y_n = True
				self.settings_print(question, sets[question], y_n)
			if(self.save_settings):
				self.write_settings()

		self.assignment_info = {}
		assignment_assignments = input("Wie viele Aufgaben hat Blatt " + str(self.assignment_number) + "?\n")

		# There is probably a better way, but this works
		# Code like this will also appear a lot in here, but I simply could not care any less
		while(not assignment_assignments or not(assignment_assignments.isdigit())):
			print("Die Anzahl der Aufgaben darf nicht leer sein und muss eine Nummer sein")
			assignment_assignments = input("Wie viele Aufgaben hat Blatt " + str(self.assignment_number) + "?\n")
		assignment_assignments = int(assignment_assignments)

		for i in range(1,assignment_assignments + 1):
			assignment_name = input("Wie heißt die " + str(i) + ". Aufgabe auf dem Zettel?\n")
			assignment_points = input("Wie viel Punkte gibt die " + str(i) + ". Aufgabe auf dem Zettel?\n")
			while(not assignment_points or not(assignment_points.isdigit())):
				print("Die Punkte für die Aufgabe dürfen nicht leer oder negativ sein und müssen eine Nummer sein")
				assignment_points = input("Wie viel Punkte gibt die " + str(i) + ". Aufgabe auf dem Zettel?\n")
			assignment_points = int(assignment_points)

			self.assignment_info[i] = [assignment_name, assignment_points]

		self.write_file()
	
	def write_file(self):
		"""
		The whole \\\\ thing may look weird, but they are actually just two escaped backslashes
		We need two Backslashes, because the first one escapes the second one in the latex file
		It works and I didn't find any better option 
		"""
		template_path = os.getcwd().replace("\\", "\\\\") + "\\\\Template\\\\"
		target_folder = self.informations["output_folder"]
		assig_nr = str(self.assignment_number) if (self.assignment_number > 9) else "0" + str(self.assignment_number)
		names = self.informations["student_names"].strip('][').replace("'", "").split(', ')

		if("%ASSIG_NR%" in target_folder):
			target_folder = target_folder.replace("%ASSIG_NR%", assig_nr)
		
		# Most operations can't handle relative file paths
		drive, path = os.path.splitdrive(target_folder)
		if not drive:
			target_folder = os.getcwd() + target_folder
		
		#Escaping, but this time for shutil
		target_folder = target_folder.replace("/", "\\")
		#Fill in "Regex"
		target_filename = self.informations["output_filename"].replace("%ASSIG_NR%", assig_nr).replace("%NAMES%", '_'.join(names)) + ".tex"

		#Copy and rename File		
		os.mkdir(target_folder)
		shutil.copy(template_path + "\\fach_uebungszettelNo_name.tex", target_folder + target_filename)
		

		# This is probably the worst part of code I have ever written but it works
		"""
		Explanation: I save every line of the template file into a list, 
		override the HARDCODED lines with the right data and overwrite the file altogether
		"""
		with open(target_folder + target_filename, "r", encoding="UTF-8") as copy:
			data = copy.readlines()

		# Location of Template src
		data[0] = "\\input{" + template_path + "\\src/header}\n"
		# Lecturer
		data[2] = "\\newcommand{\\dozent}{" + self.informations["lecturer_name"] +  "}\n"
		# Tutor
		data[3] = "\\newcommand{\\tutor}{" + self.informations["tutor_name"] + "}\n"
		# Tutorial Number
		data[4] = "\\newcommand{\\tutoriumNo}{"+ self.informations["tutorial_number"] + "}\n"
		# Assignment Number
		data[5] = "\\newcommand{\\ubungNo}{"+ assig_nr + "}\n"
		# Lecture Name
		data[6] = "\\newcommand{\\veranstaltung}{"+ self.informations["lecture_name"] +"}\n"
		# Semester
		data[7] = "\\newcommand{\\semester}{" + self.informations["semester_id"]+"}\n"
		#Names
		data[8] = "\\newcommand{\\studenten}{"+ ', '.join(names) + "}\n"
		#Titlepage
		data[12] = "\\input{" + template_path + "\\src/titlepage}\n\n\n"

		# I'm not gonna explain much here, since I literally will never look at this code again, I'm ashamed of it
		i = 13
		for assignment in self.assignment_info:
			if(i < len(data)):
				data[i] = "% /////////////////////// Aufgabe " + str(assignment) + "/////////////////////////\n"
				i += 1
			else:
				data = data + ["% /////////////////////// Aufgabe " + str(assignment) + "/////////////////////////\n"]
			if(i < len(data)):
				data[i] = "\\section{Aufgabe: " + self.assignment_info[assignment][0] + " \\hfill (" + str(self.assignment_info[assignment][1]) +" Punkte)}\n"
				i+=1
			else:
				data = data + ["\\section{Aufgabe: " + self.assignment_info[assignment][0] + " \\hfill (" + str(self.assignment_info[assignment][1]) +" Punkte)}\n"]

		if(i < len(data)):
			data[i] = "% /////////////////////// END DOKUMENT /////////////////////////\n"
			i+=1
			if (i < len(data)):
		 		data[i] = "\\end{document}"
			else:
				data = data + "\\end{document}"
		else:
			data = data + ["% /////////////////////// END DOKUMENT /////////////////////////\n\\end{document}"]

		with open(target_folder + target_filename, "w", encoding="UTF-8") as outfile:
			outfile.writelines(data)

	def get_last_assignment(self):
		# "Intelligent" Assignment Number Finding

		folder = self.informations["output_folder"]
		
		# Remove the Parts that contain the Assignment Number so we have the parent folder of the path
		if("%ASSIG_NR%" in folder):
			folder = re.sub(r"[\w ]*%ASSIG_NR%[\w ]*/","", folder)
		
		drive, path = os.path.splitdrive(folder)
		if not drive:
			folder = os.getcwd() + folder
		
		# Find the biggest Number in the folder (this PROBABLY causes problems, but not my machine)
		biggest = 0
		for name in os.listdir(folder):
			if bool(re.search(r"\d\d",name)):
				num = int(re.search(r"\d\d", name).group())
				biggest = num if num > biggest else biggest
		
		return biggest if biggest > 0 else False


	def settings_print(self, settings_key, settings_text, is_y_n = False):
		# Simple script to guarantee the right inputs

		res = input(settings_text)
		while(not(settings_key == "output_path") and not res):
			print("Dieses Feld darf nicht leer sein")
			res = input(settings_text)

		while(is_y_n and not(res == "y" or res == "n")):
			print("Dieses Feld muss entweder y oder n sein")
			res = input(settings_text)

		if settings_key == "output_filename":
			if not res:
				res = "Blatt_%ASSIG_NR%_%NAMES%"
			else:
				while (not("%ASSIG_NR%" in res) and not("%NAMES%" in res)):
					if not res:
						res = "Blatt_%ASSIG_NR%_%NAMES%"
						break
					print("Es müssen jeweils mindestens einmal %ASSIG_NR% und %NAMES% im Namen vorkommen")
					res = input(settings_text)

		if settings_key == "save_settings":
			self.save_settings =  True if (res == "y") else False
			return
		
		if settings_key == "assignment_number":
			self.assignment_number =  res
			return

		if settings_key == "student_names":
			if ", " in res:
				res = res.split(", ")
			else:
				res = res.split(",")

		if res == "y" or res == "n":
			res = True if (res == "y") else False
		self.informations[settings_key] = res

	def write_settings(self):
		# Write settings to json file
		information_comments = {
			"lecturer_name": "Name des Dozenten/der Dozentin", 
			"tutor_name": "Name des Tutors/der Tutorin", 
			"tutorial_number": "Nummer des Tutoriums",
			"lecture_name": "Name der Veranstaltung",
			"semester_id": "Semester",
			"student_names": "Name der Student*Innen",
			"output_folder": "Output Ordner",
			"output_filename": "Namen Schema",
			"auto_increment": "Arbeitsblätter automatisch hochzählen",
			"auto_increment_steps": "Schritte beim Hochzählen"
			}
		
		# This would be faster with json plugins, but I want to write comments
		f = open("makefile_settings.json", "a", encoding="UTF-8")
		f.write("{\n")
		i = 0
		for setting in self.informations:
			write_string = "\t\"_comment%d\": \"%s\",\n\t\"%s\": \"%s\",\n\n" % (i,information_comments[setting], setting, self.informations[setting])
			if(i == (len(self.informations) -1)):
				write_string = write_string[:-3]
			f.write(write_string)
			i+=1
		f.write("\n}")
		f.close()

	def settings_exist(self):
		return os.path.isfile('./makefile_settings.json')

# Call everything
Makefile()