import datetime
import requests 
import numpy as np
from PIL import Image
from bbox import BBox2D
from PIL import Image
import numpy as np
from scipy import spatial
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import extcolors
from colormap import rgb2hex
import re #re sta per regular expression
import numpy as np
import pandas as pd
import csv
import webcolors
import json
from colori import A,B
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
import extcolors
from colormap import rgb2hex
import base64 #mi serve per convertire l'immagine in base64
import matplotlib.pyplot as plt
from aenum import MultiValueEnum
from matplotlib.colors import BoundaryNorm, ListedColormap
from sentinelhub import CRS, BBox, DataCollection, SHConfig
from eolearn.core import EOWorkflow, FeatureType, LoadTask, OutputTask, SaveTask, linearly_connect_tasks
from eolearn.io import SentinelHubDemTask, SentinelHubEvalscriptTask, SentinelHubInputTask
import pymongo 
import gridfs
from pymongo import MongoClient
import os
from bson.binary import Binary
import gridfs
import cv2
from mongoengine import connect,Document,fields


client = pymongo.MongoClient("mongodb+srv://root:root@cluster0.xgcayna.mongodb.net/?retryWrites=true&w=majority")
db = client.test

rawl2a = db.rawl2a
rawclc = db.rawclc
analisiL2A = db.analisiL2A
analisiCLC = db.analisiCLC

class SCL(MultiValueEnum):
    """Enum class containing basic LULC types"""

    NO_DATA = "no data", 0, "#000000"
    IMAGE_BORDE = "image border", 1, '#ffffff'
    URBAN_TRAFIC = "urban trafic", 2, "#ff0004"
    ROADS = "roads", 3, "#868686"
    URBAN_CITY = "urban city", 4, "#774c0b"
    VEGETATION = "vegetation", 5, "#10d32d"
    LAKES_SEA = "lakes/sea", 6, "#0000ff"
    CLOUDS_LOW_PROBA = "clouds low proba.", 7, "#818181"
    PORT_AREAS = "port areas", 8, "#c0c0c0"
    CLOUDS_HIGH_PROBA = "clouds high proba.", 9, "#f2f2f2"
    SNOW_ICE = "snow / ice", 10, "#53fffa"
    INDUSTRIAL_COMMERCIAL_TRANSPORT = "industrial/commercial/transport", 11, "#c8a1ff"
    LANDFILLS = "landfills",12, "#a64d00"
    AIRPORTS = "airports",13, "#e6cce6"

    @property
    def rgb(self):
        return [c / 255.0 for c in self.rgb_int]

    @property
    def rgb_int(self):
        hex_val = self.values[2][1:]
        return [int(hex_val[i : i + 2], 16) for i in (0, 2, 4)]

CLIENT_ID = "8db600e0-a6bb-4396-a084-23639d294dab"
CLIENT_SECRET = "uOr2-Ii99hFB1YdopC24X^vkNHmc4}@S5W)3S{|D"

config = SHConfig()

if CLIENT_ID and CLIENT_SECRET:
    config.sh_client_id = CLIENT_ID
    config.sh_client_secret = CLIENT_SECRET

if config.sh_client_id == "" or config.sh_client_secret == "" or config.instance_id == "":
    print("Warning! To use Sentinel Hub services, please provide the credentials (client ID and client secret).")

#cities=['palermo']
#cities = ['bari','cosenza','napoli','salerno'] 
#cities = ['firenze']
#cities = ['torino']
#cities = ['roma']
cities = ['milano']



for citta in cities :

    req = requests.get(f"https://nominatim.openstreetmap.org/search?city={citta}&format=json").json()[0]["boundingbox"]
    box2=BBox([req[2],req[0],req[3],req[1]], crs=CRS.WGS84)
    partizioni =box2.get_partition(3,3)
    cont=0
    conta=0
    contaa=0
    time_interval = ("2021-10-01", "2021-12-10")
    data_eff="2021-11-08"
    dizl2a={"citta":citta, "data":data_eff, "immagini":[]}
    dizclc={"citta":citta, "data":data_eff, "immagini":[]}

    dizanalisil2a={"citta":citta, "data":data_eff}
    dizanalisiclc={"citta":citta, "data":data_eff}


    for part in partizioni:
        for box in part:
            jsonImmagine = {"bbox":str(box)}
            print(box) #stampa il bbox
            
            # time interval of downloaded data
            time_interval = ("2021-10-01", "2021-12-10")
        

            # resolution of the request (in metres)
            resolution = 20

            time_difference = datetime.timedelta(hours=2)


            indices_evalscript = """
                //VERSION=3

                function setup() {
                    return {
                        input: ["B03","B04","B08","dataMask"],
                        output:[{
                            id: "indices",
                            bands: 2,
                            sampleType: SampleType.FLOAT32
                        }]
                    }
                }

                function evaluatePixel(sample) {
                    let ndvi = index(sample.B08, sample.B04);
                    let ndwi = index(sample.B03, sample.B08);
                    return {
                    indices: [ndvi, ndwi]
                    };
                }
            """

            add_dem = SentinelHubDemTask(data_collection=DataCollection.DEM_COPERNICUS_30, resolution=resolution, config=config)

            add_l2a_and_scl = SentinelHubInputTask(
                data_collection=DataCollection.SENTINEL2_L2A,
                bands=["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"],
                bands_feature=(FeatureType.DATA, "L2A_" + str(conta)),
                additional_data=[(FeatureType.MASK, "SCL")],
                resolution=resolution,
                time_difference=time_difference,
                config=config,
                max_threads=10,
            )

            save = SaveTask("io_example", overwrite_permission=2, compress_level=1)

            output_task = OutputTask("eopatch")

            workflow_nodes = linearly_connect_tasks(add_l2a_and_scl, add_dem, save, output_task)
            workflow = EOWorkflow(workflow_nodes)

            result = workflow.execute(
                {
                    workflow_nodes[0]: {"bbox": box, "time_interval": time_interval},
                    workflow_nodes[-2]: {"eopatch_folder": "eopatch"},
                }
            )

            eopatch = result.outputs["eopatch"]

            eopatch.plot((FeatureType.DATA, "L2A_" + str(conta)), times=[3], rgb=[3, 2, 1])
            plt.axis(False)
            plt.savefig("L2A_"+ citta +  "_" + str(time_interval) + "_" + str(cont) + ".png")

            
            with open("L2A_"+ citta +  "_" + str(time_interval) + "_" + str(cont) + ".png","rb") as img_fileL2A:
                 my_stringL2A = base64.b64encode(img_fileL2A.read())
            print(my_stringL2A)

            jsonImmagine["byte64"]=my_stringL2A
            print(len(jsonImmagine["byte64"]))
            dizl2a["immagini"].append(jsonImmagine)
                
            #del jsonImmagine["byte64"]
            
        
            #INIZIO CLC ,LA CLASSE CON I COLORI E' ALL'INIZIO DEL FILE
            scl_bounds = [-0.5 + i for i in range(len(SCL) + 1)]
            scl_cmap = ListedColormap([x.rgb for x in SCL], name="scl_cmap")
            scl_norm = BoundaryNorm(scl_bounds, scl_cmap.N)

            fig, ax = plt.subplots(1, 1, figsize=(10, 10))
            im = plt.imshow(eopatch.mask["SCL"][3].squeeze(), cmap=scl_cmap, norm=scl_norm)
            plt.axis(False)

           
            plt.savefig("CLC_"+ citta +  "_" + str(time_interval) + "_" +  str(cont) +".png",bbox_inches='tight',pad_inches = 0) #i due campi finali tolgono i bordi bianchi bbox_inches='tight',pad_inches = 0
            

            
            with open("CLC_"+ citta +  "_" + str(time_interval) + "_" +  str(cont) +".png","rb") as img_fileCLC:
                my_stringCLC = base64.b64encode(img_fileCLC.read())
            print(my_stringCLC)

            jsonImmagine["byte64"]=my_stringCLC
            print(len(jsonImmagine["byte64"]))
            dizclc["immagini"].append(jsonImmagine)



            load = LoadTask("io_example")
            new_eopatch = load.execute(eopatch_folder="eopatch")
            
            cont +=1
            conta +=1
    rawl2a.insert_one(dizl2a)
    rawclc.insert_one(dizclc)
    #MERGE L2A

    image0 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_0.png').resize((800, 800))
    image1 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_1.png').resize((800, 800))
    image2 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_2.png').resize((800, 800))
    image3 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_3.png').resize((800, 800))
    image4 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_4.png').resize((800, 800))
    image5 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_5.png').resize((800, 800))
    image6 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_6.png').resize((800, 800))
    image7 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_7.png').resize((800, 800))
    image8 = Image.open('L2A_'+citta + "_" + str(time_interval) +'_8.png').resize((800, 800))
    image1_size = image1.size
    new_image = Image.new('RGB',(3*image1_size[0],3* image1_size[1]), (250,250,250))

    #Le immagini vengono inserite dal basso verso l'alto

    #Primo blocco di immagini
    new_image.paste(image0,(0,1600)) #0 è la x, 1600 è la y
    new_image.paste(image1,(0,800))
    new_image.paste(image2,(0,0))

    #Secondo blocco di immagini
    new_image.paste(image3,(800,1600))
    new_image.paste(image4,(800,800))
    new_image.paste(image5,(800,0))

    #Terzo blocco di immagini
    new_image.paste(image6,(1600,1600))
    new_image.paste(image7,(1600,800))
    new_image.paste(image8,(1600,0))


    new_image.save("mergeL2A_"+ citta + "_" + str(time_interval) + ".png")

    with open("mergeL2A_"+ citta + "_" + str(time_interval) + ".png","rb") as img_fileMergeL2A:
        my_stringMergeL2A = base64.b64encode(img_fileMergeL2A.read())
    print(my_stringMergeL2A)

    dizanalisil2a["immagine"]=my_stringMergeL2A

    #MERGE CLC
    clc0 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_0.png').resize((800, 800))
    clc1 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_1.png').resize((800, 800))
    clc2 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_2.png').resize((800, 800))
    clc3 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_3.png').resize((800, 800))
    clc4 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_4.png').resize((800, 800))
    clc5 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_5.png').resize((800, 800))
    clc6 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_6.png').resize((800, 800))
    clc7 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_7.png').resize((800, 800))
    clc8 = Image.open('CLC_'+citta + "_" + str(time_interval) + '_8.png').resize((800, 800))
    clc9 = Image.open("legenda clc.png").resize((2000,500)) #è la legenda 
    clc1_size = clc1.size
    new_imageclc = Image.new('RGB',(3*clc1_size[0],4* clc1_size[1]), (250,250,250))

    #Le immagini vengono inserite dal basso verso l'alto

    #Primo blocco di immagini
    new_imageclc.paste(clc0,(0,1600)) #0 è la x, 1600 è la y
    new_imageclc.paste(clc1,(0,800))
    new_imageclc.paste(clc2,(0,0))

    #Secondo blocco di immagini
    new_imageclc.paste(clc3,(800,1600))
    new_imageclc.paste(clc4,(800,800))
    new_imageclc.paste(clc5,(800,0))

    #Terzo blocco di immagini
    new_imageclc.paste(clc6,(1600,1600))
    new_imageclc.paste(clc7,(1600,800))
    new_imageclc.paste(clc8,(1600,0))
    new_imageclc.paste(clc9,(200,2500)) #aggiungo la legenda sotto a tutto

    new_imageclc.save("mergeCLC_"+ citta + "_" + str(time_interval) + ".png")

    with open("mergeCLC_"+ citta + "_" + str(time_interval) + ".png","rb") as img_fileMergeCLC:
        my_stringMergeCLC = base64.b64encode(img_fileMergeCLC.read())
    print(my_stringMergeCLC)

    dizanalisiclc["immagine"]=my_stringMergeCLC


    #FILE .json PER L2A

    def color_name(pt):
        RGB= np.delete(A, np.s_[3:5], axis=1)


        P=A[spatial.KDTree(A).query(pt)[1]] #interroga l'albero(che sarebbe A, contiene la lista dei vari colori in formato RGB) per trovare i valori più vicini
        #print (P) #stampa il colore più vicino in formato RGB

    #in B c'è la lista dei colori in formato RGB-COLOR-NAME-HEX
        for k in B:
                if (int(k[0]) == P[0]) and (int(k[1]) == P[1]) and (int(k[2]) == P[2]): 
                    return (k[3]) #stampa il nome del colore


    #Restituisce valori RGB se l'argomento hsl = False else restituisce valori HSL.
    def hex_to_rgb(hx, hsl=False):
        if re.compile(r'#[a-fA-F0-9]{3}(?:[a-fA-F0-9]{3})?$').match(hx):
            div = 255.0 if hsl else 0
            if len(hx) <= 4:
                return tuple(int(hx[i]*2, 16) / div if div else
                            int(hx[i]*2, 16) for i in (1, 2, 3))
            return tuple(int(hx[i:i+2], 16) / div if div else
                        int(hx[i:i+2], 16) for i in (1, 3, 5))
        raise ValueError(f'"{hx}" is not a valid HEX code.')



    #estraiamo il colore con la libreria extcolors,
    #tolleranza: raggruppa i colori per dare una migliore 
    #rappresentazione visiva. Scala da 0 a 100, dove 0 non raggruppa nessun colore e 100 raggruppa i colori tutto in uno
    #limite superiore al numero di colori estratti presentati nell'output.
    colors_x = extcolors.extract_from_path("mergeL2A_"+ citta + "_" + str(time_interval) + ".png", tolerance = 10, limit = 20)

    


    #funzione che converte i codici RGB in codici colore HEX con la libreria rgb2hexe e crea un dataframe di memorizzazione
    #RGB(119,163,69) il corrispondente HEX #77a345
    def color_to_df(input):
        colors_pre_list = str(input).replace('([(','').split(', (')[0:-1]
        df_rgb = [i.split('), ')[0] + ')' for i in colors_pre_list]
        df_percent = [i.split('), ')[1].replace(')','') for i in colors_pre_list]
        
        
        df_color_up = [rgb2hex(int(i.split(", ")[0].replace("(","")),
                            int(i.split(", ")[1]),
                            int(i.split(", ")[2].replace(")",""))) for i in df_rgb]
        
        df = pd.DataFrame(zip(df_color_up, df_percent), columns = ['c_code','occurence'])
        return df

    df_color = color_to_df(colors_x)

    list_color = list(df_color['c_code'])
    list_precent = [int(i) for i in list(df_color['occurence'])]
    dizionario = {}
    for p in range(len(list_precent)-1):
        
        text_c_json= {}
        text_c_json['perc']=round(list_precent[p]*100/sum(list_precent),1)
        text_c_json['valore']= list_precent[p]
        text_c_json['hex']=list_color[p]
        text_c_json['rgb']= hex_to_rgb(list_color[p])
        
        if color_name(hex_to_rgb(list_color[p])) in dizionario.keys():
            jsonpreso= dizionario[color_name(hex_to_rgb(list_color[p]))]
            text_c_json['perc']+=jsonpreso['perc']
            dizionario [color_name(hex_to_rgb(list_color[p]))] = text_c_json
        else:
            dizionario [color_name(hex_to_rgb(list_color[p]))] = text_c_json

    with open(citta + "_" + str(time_interval) + "_" + "L2A.json","w") as fw:
        json.dump(dizionario, fw)

    dizanalisil2a["percentuali"]=dizionario
    
    

    analisiL2A.insert_one(dizanalisil2a)
    



    #FILE .json PER IL CLC

    def color_name(pt):
        RGB= np.delete(A, np.s_[3:5], axis=1)


        P=A[spatial.KDTree(A).query(pt)[1]] #interroga l'albero(che sarebbe A, contiene la lista dei vari colori in formato RGB) per trovare i valori più vicini
        #print (P) #stampa il colore più vicino in formato RGB

    #in B c'è la lista dei colori in formato RGB-COLOR-NAME-HEX
        for k in B:
                if (int(k[0]) == P[0]) and (int(k[1]) == P[1]) and (int(k[2]) == P[2]): 
                    return (k[3]) #stampa il nome del colore


    #Restituisce valori RGB se l'argomento hsl = False else restituisce valori HSL.
    def hex_to_rgb(hx, hsl=False):
        if re.compile(r'#[a-fA-F0-9]{3}(?:[a-fA-F0-9]{3})?$').match(hx):
            div = 255.0 if hsl else 0
            if len(hx) <= 4:
                return tuple(int(hx[i]*2, 16) / div if div else
                            int(hx[i]*2, 16) for i in (1, 2, 3))
            return tuple(int(hx[i:i+2], 16) / div if div else
                        int(hx[i:i+2], 16) for i in (1, 3, 5))
        raise ValueError(f'"{hx}" is not a valid HEX code.')



    #estraiamo il colore con la libreria extcolors,
    #tolleranza: raggruppa i colori per dare una migliore 
    #rappresentazione visiva. Scala da 0 a 100, dove 0 non raggruppa nessun colore e 100 raggruppa i colori tutto in uno
    #limite superiore al numero di colori estratti presentati nell'output.
    colors_x = extcolors.extract_from_path("mergeCLC_"+ citta + "_" + str(time_interval) + ".png", tolerance = 10, limit = 20)


    #funzione che converte i codici RGB in codici colore HEX con la libreria rgb2hexe e crea un dataframe di memorizzazione
    #RGB(119,163,69) il corrispondente HEX #77a345
    def color_to_df(input):
        colors_pre_list = str(input).replace('([(','').split(', (')[0:-1]
        df_rgb = [i.split('), ')[0] + ')' for i in colors_pre_list]
        df_percent = [i.split('), ')[1].replace(')','') for i in colors_pre_list]
        
        
        df_color_up = [rgb2hex(int(i.split(", ")[0].replace("(","")),
                            int(i.split(", ")[1]),
                            int(i.split(", ")[2].replace(")",""))) for i in df_rgb]
        
        df = pd.DataFrame(zip(df_color_up, df_percent), columns = ['c_code','occurence'])
        return df

    df_color = color_to_df(colors_x)


    list_color = list(df_color['c_code'])
    list_precent = [int(i) for i in list(df_color['occurence'])]
    dizionario = {}
    for p in range(len(list_precent)-1):
        
        text_c_json= {}
        text_c_json['perc']=round(list_precent[p]*100/sum(list_precent),1)
        text_c_json['valore']= list_precent[p]
        text_c_json['hex']=list_color[p]
        text_c_json['rgb']= hex_to_rgb(list_color[p])
        
        if color_name(hex_to_rgb(list_color[p])) in dizionario.keys():
            jsonpreso= dizionario[color_name(hex_to_rgb(list_color[p]))]
            text_c_json['perc']+=jsonpreso['perc']
            dizionario [color_name(hex_to_rgb(list_color[p]))] = text_c_json
        else:
            dizionario [color_name(hex_to_rgb(list_color[p]))] = text_c_json

    with open(citta + "_" + str(time_interval) + "_" + "CLC.json","w") as fw:
        json.dump(dizionario, fw)


    dizanalisiclc["percentuali"]=dizionario
    
    

    analisiCLC.insert_one(dizanalisiclc)


    
    #GRAFICO PER MERGE L2A
    #estraiamo il colore con la libreria extcolors,
    #tolleranza: raggruppa i colori per dare una migliore 
    #rappresentazione visiva. Scala da 0 a 100, dove 0 non raggruppa nessun colore e 100 raggruppa i colori tutto in uno
    #limite superiore al numero di colori estratti presentati nell'output.
    colors_x = extcolors.extract_from_path("mergeL2A_"+ citta + "_" + str(time_interval) + ".png", tolerance = 10, limit = 10)


    #funzione che converte i codici RGB in codici colore HEX con la libreria rgb2hexe e crea un dataframe di memorizzazione
    #RGB(119,163,69) il corrispondente HEX #77a345
    def color_to_df(input):
        colors_pre_list = str(input).replace('([(','').split(', (')[0:-1]
        df_rgb = [i.split('), ')[0] + ')' for i in colors_pre_list]
        df_percent = [i.split('), ')[1].replace(')','') for i in colors_pre_list]
        
        
        df_color_up = [rgb2hex(int(i.split(", ")[0].replace("(","")),
                            int(i.split(", ")[1]),
                            int(i.split(", ")[2].replace(")",""))) for i in df_rgb]
        
        df = pd.DataFrame(zip(df_color_up, df_percent), columns = ['c_code','occurence'])
        return df

    df_color = color_to_df(colors_x)

    #in questo modo realizziamo il grafico a ciambella per visualizzare il risultato
    list_color = list(df_color['c_code'])
    list_precent = [int(i) for i in list(df_color['occurence'])]
    text_c = [c + ' ' + str(round(p*100/sum(list_precent),1)) +'%' for c, p in zip(list_color,
                                                                                list_precent)]
    fig, ax = plt.subplots(figsize=(90,90),dpi=10)
    wedges, text = ax.pie(list_precent,
                        labels= text_c,
                        labeldistance= 1.05,
                        colors = list_color,
                        textprops={'fontsize': 40, 'color':'black'}
                        )
    plt.setp(wedges, width=0.3)

    #creaimo uno spazio al centro per raffigurare il grafico e lo mostriamo
    plt.setp(wedges, width=0.36)

    ax.set_aspect("equal")
    fig.set_facecolor('white')
    plt.savefig(citta + "graficoL2A_" + str(time_interval) + "_.png")

    #GRAFICO PER MERGE CLC
    #estraiamo il colore con la libreria extcolors,
    #tolleranza: raggruppa i colori per dare una migliore 
    #rappresentazione visiva. Scala da 0 a 100, dove 0 non raggruppa nessun colore e 100 raggruppa i colori tutto in uno
    #limite superiore al numero di colori estratti presentati nell'output.
    colors_x = extcolors.extract_from_path("mergeCLC_"+ citta + "_" + str(time_interval) + ".png", tolerance = 10, limit = 10)


    #funzione che converte i codici RGB in codici colore HEX con la libreria rgb2hexe e crea un dataframe di memorizzazione
    #RGB(119,163,69) il corrispondente HEX #77a345
    def color_to_df(input):
        colors_pre_list = str(input).replace('([(','').split(', (')[0:-1]
        df_rgb = [i.split('), ')[0] + ')' for i in colors_pre_list]
        df_percent = [i.split('), ')[1].replace(')','') for i in colors_pre_list]
        
        
        df_color_up = [rgb2hex(int(i.split(", ")[0].replace("(","")),
                            int(i.split(", ")[1]),
                            int(i.split(", ")[2].replace(")",""))) for i in df_rgb]
        
        df = pd.DataFrame(zip(df_color_up, df_percent), columns = ['c_code','occurence'])
        return df

    df_color = color_to_df(colors_x)

    #in questo modo realizziamo il grafico a ciambella per visualizzare il risultato
    list_color = list(df_color['c_code'])
    list_precent = [int(i) for i in list(df_color['occurence'])]
    text_c = [c + ' ' + str(round(p*100/sum(list_precent),1)) +'%' for c, p in zip(list_color,
                                                                                list_precent)]
    fig, ax = plt.subplots(figsize=(90,90),dpi=10)
    wedges, text = ax.pie(list_precent,
                        labels= text_c,
                        labeldistance= 1.05,
                        colors = list_color,
                        textprops={'fontsize': 40, 'color':'black'}
                        )
    plt.setp(wedges, width=0.3)

    #creaimo uno spazio al centro per raffigurare il grafico e lo mostriamo
    plt.setp(wedges, width=0.36)

    ax.set_aspect("equal")
    fig.set_facecolor('white')
    plt.savefig(citta + "graficoCLC_" + str(time_interval) + "_.png")
