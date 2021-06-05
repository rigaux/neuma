from django import template
#from django.utils.datastructures import SortedDict
from collections import OrderedDict
from fractions import Fraction


register = template.Library()

@register.filter(name='sort')
def listsort(value):
    if isinstance(value, dict):
        new_dict = OrderedDict()
        key_list = sorted(value.keys())
        for key in key_list:
            new_dict[key] = value[key]
        return new_dict
    elif isinstance(value, list):
        return sorted(value)
    else:
        return value
    listsort.is_safe = True


@register.filter(name='semitones')
def semitoneconv(value):
    if(value==0):
        return '"0"'
    elif(value==1):
        return '"asc minor 2nd"'
    elif(value==2):
        return '"asc major 2nd"'
    elif(value==3):
        return '"asc minor 3rd"'
    elif(value==4):
        return '"asc major 3rd"'
    elif(value==5):
        return '"asc 4th"'
    elif(value==5):
        return '"tritone"'
    elif(value==7):
        return '"asc 5th"'
    elif(value==8):
        return '"asc minor 6th"'
    elif(value==9):
        return '"asc major 6th"'
    elif(value==10):
        return '"asc minor 7th"'
    elif(value==11):
        return '"asc major 7th"'
    elif(value==12):
        return '"asc octave"'
    elif(value==13):
        return '"asc minor 9th"'
    elif(value==14):
        return '"asc major 9th"'
    elif(value==15):
        return '"asc minor 10th"'
    elif(value==16):
        return '"asc major 10th"'
    elif(value==17):
        return '"asc 11th"'
    elif(value==18):
        return '"asc augmented 11th"'
    elif(value==-1):
        return '"desc minor 2nd"'
    elif(value==-2):
        return '"desc major 2nd"'
    elif(value==-3):
        return '"desc minor 3rd"'
    elif(value==-4):
        return '"desc major 3rd"'
    elif(value==-5):
        return '"desc 4th"'
    elif(value==-5):
        return '"tritone"'
    elif(value==-7):
        return '"desc 5th"'
    elif(value==-8):
        return '"desc minor 6th"'
    elif(value==-9):
        return '"desc major 6th"'
    elif(value==-10):
        return '"desc minor 7th"'
    elif(value==-11):
        return '"desc major 7th"'
    elif(value==-12):
        return '"desc octave"'
    elif(value==-13):
        return '"desc minor 9th"'
    elif(value==-14):
        return '"desc major 9th"'
    elif(value==-15):
        return '"desc minor 10th"'
    elif(value==-16):
        return '"desc major 10th"'
    elif(value==-17):
        return '"desc 11th"'
    elif(value==-18):
        return '"desc augmented 11th"'
    else:
        return '"'+str(value)+'"'


@register.filter(name='keysig')
def keysignature(value):
    # -7 > index0, 0 > index 7, etc.
    v = ['Cb/Abm','Gb/Ebm','Db/Bbm','Ab/Fm','Eb/Cm','Eb/Gm','F/Dm','C/Am',
         'G/Em','D/Bm','A/F#m','E/C#m','B/G#m','F#/D#m','C#/A#m']
    try:
        a = v[value+7]
        return a
    except:
        return 'Wrong value for keysignature'

@register.filter(name='percent')
def templatetag_topercent(value):
    return str(int(10000*value)/100)+'%'



@register.filter(name='scale_degree')
def scale_degree(value):
    # -7 > index0, 0 > index 7, etc.
    v = ['Tonic','[not minor/major scale]','Supertonic','Mediant (minor)',
         'Mediant (major)','Subdominant','[not minor/major scale]','Dominant',
         'Submediant (minor)','Submediant (major)','Subtonic','Leading tone']
    try:
        a = v[value]
        return '"'+a+'"'
    except:
        return '"Wrong value for degree"'


@register.filter(name='rhythm_figures_print')
def rhythm_figures_print(value):
    if(value==Fraction(4,1)):
        return '"Whole"'
    if(value==Fraction(3,1)):
        return '"Dotted Half"'
    if(value==Fraction(2,1)):
        return '"Half"'
    if(value==Fraction(3,2)):
        return '"Dotted quarter"'
    if(value==Fraction(1,1)):
        return '"Quarter"'
    if(value==Fraction(1,2)):
        return '"Eighth"'
    if(value==Fraction(1,4)):
        return '"Sixteenth"'
    if(value==Fraction(1,3)):
        return '"[Third]"'
    if(value==Fraction(3,4)):
        return '"Dotted Eight"'
    return '"'+str(value)+'"'


@register.filter(name='sp36')
def sp36(value):
    return str(float(value)*36)

#@register.filter(name='tocolor')
#def tocolor(value):
#    return "rgb("+str(int(value*10))+","+
#                  str(int(255-value*10))+','+
#                  str(int(127+value*5))+')'

@register.filter(name='nrange')
def nrange(value):
    return range(value)


@register.filter(name='print_histogram')
def print_histogram(histo):
    uid = histo.generate_uid()

    labels_l = map(lambda x:histo.labelling_closure(x),histo.labels)
    labels = "["+",".join(list(labels_l))+"]"
    #[{% for k,i in voice.get_pitches.items|sort %}"{{k}}",{% endfor %}]

    data_l = map(lambda x:str(x),histo.data)
    data = "["+",".join(list(data_l))+"]"
    #[{% for k,i in voice.get_pitches.items|sort %}"{{i|stringformat:"f"}}",{% endfor %}]

    #rgba(232,99,55,0.5)

    s  = '<canvas id="'+uid+'" class="neuma-stat-histogram"></canvas>'
    s += '''<script>
        var pitches_ctx = document.getElementById("'''+uid+'''");
        var pitches_data = {
            labels: '''+labels+''',
            datasets: [
                {
                    label: "'''+histo.title+'''",
                    backgroundColor: "#'''+histo.color+'''",
                    borderColor: "#'''+histo.color+'''",
                    borderWidth: 1,
                    hoverBackgroundColor: "#'''+histo.color+'''",
                    hoverBorderColor: "rgba(0,0,0,1)",
                    data: '''+data+''',
                }
            ]
        };
        var pitches_chart = new Chart(pitches_ctx, {
            type: 'bar',
            data: pitches_data,
            options: {
                scales: {
                    yAxes: [{
                        ticks: {
                            beginAtZero:true
                        }
                    }]
                }
            }
        });
    </script>'''

    return s
