import pandas as pd

df_m = pd.read_csv('melodic_selected.csv', names = ["pattern", "freq"])
df_d = pd.read_csv('diatonic_selected.csv', names = ["pattern", "freq"])
df_r = pd.read_csv('rhythmic_selected.csv', names = ["pattern", "freq"])

mm = df_m['pattern'].to_list()
dd = df_d['pattern'].to_list()
rr = df_r['pattern'].to_list()

#1 ; = 3 intervals, 1* 3-grams
#2 ; = 4 intervals, 2* 3-grams

def intervals_to_ngrams(list, NGRAM_SIZE = 3):
        #
        #   Splits intervals into ngrams with size NGRAM_SIZE, for both melodic and diatonic searches
        #
        nb_codes = len(list)
        phrase = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            #ngram no longer needs to begin with a separator ';' because it's absolute value
            ngram = ""
            for j in range(i, i + NGRAM_SIZE): 
                ngram = ngram + str(list[j]) + ";"
            phrase += ngram + " N "
        return phrase

def rhythms_to_ngrams(list, NGRAM_SIZE = 3):
        #
        #   Splits rhythms ratios into ngrams with size NGRAM_SIZE, e.g : (3/4)(2/3)(1/2) (2/3)(1/2)(1/2) ...
        #
        nb_codes = len(list)
        text = ""
        for i in range(nb_codes - NGRAM_SIZE + 1):
            ngram = ""
            for j in range(i, i + NGRAM_SIZE):
                # Surround ratios with parentheses
                ngram += "(" + str(list[j]) + ")"
            text += ngram + " N "
        return text

m = []
for item in mm:
	interval = []
	word = ""
	for j in item:
		if j == ';':
			interval.append(word)
			word = ""
		elif j != ' ':
			word = word + str(j)
	queryphrase = intervals_to_ngrams(interval)
	queryphrase = queryphrase[:-1]
	m.append(queryphrase)

newm = []
for i in m:
	newm.append('SELECT * FROM public.\"Descriptor\" WHERE value LIKE \'%'+ i + '%\' and type = \'melody\'') 

d = []
for item in dd:
	interval = []
	word = ""
	for j in item:
		if j == ';':
			interval.append(word)
			word = ""
		elif j != ' ':
			word = word + str(j)
	queryphrase = intervals_to_ngrams(interval)
	queryphrase = queryphrase[:-1]
	d.append(queryphrase)

newd = []
for i in d:
	newd.append('SELECT * FROM public.\"Descriptor\" WHERE value LIKE \'%'+ i + '%\' and type = \'diatonic\'') 

r = []
for item in rr:
	interval = []
	word = ""
	for j in item:
		if j == ')':
			interval.append(word)
			word = ""
		elif j != ' ' and j != '(':
			word = word + str(j)
	queryphrase = rhythms_to_ngrams(interval)
	r.append(queryphrase)

newr = []
for i in r:
	newr.append('SELECT * FROM public.\"Descriptor\" WHERE value LIKE \'%'+ i + '%\'')

'''
#When there is no need to re-output the commands I comment this part.

with open("sqlcommands.txt", "w") as o:
	for i in newm:
		o.write(i)
		o.write(';\n')
	for i in newd:
		o.write(i)
		o.write(';\n')
	for i in newr:
		o.write(i)
		o.write(';\n')
'''

len_m = len(newm) 
len_d = len(newd) 
len_r = len(newr) 

result = open('result.txt', "r")
Lines = result.readlines()

time_m = []
time_d = []
time_r = []

count = 0
for line in Lines:
	#melodic part
	if count < len_m:
		time_m.append(line[6:])
	#diatonic part
	elif count >= len_m and count < len_m + len_d:
		time_d.append(line[6:])
	#rhythmic part
	elif count >= len_m + len_d and count < len_m + len_d + len_r:
		time_r.append(line[6:])
	count+=1

dict_m = {'melodic':mm, 'time': time_m}
dict_d = {'diatonic':dd, 'time':time_d}
dict_r = {'rhythmic':rr, 'time':time_r}


df_newm = pd.DataFrame(data=dict_m)
df_newd = pd.DataFrame(data=dict_d)
df_newr = pd.DataFrame(data=dict_r)

df_newm.to_csv('melodic_time.csv', index=False)
df_newd.to_csv('diatonic_time.csv', index=False)
df_newr.to_csv('rhythmic_time.csv', index=False)
