from keras.preprocessing import image
from keras.applications.inception_resnet_v2 import InceptionResNetV2
from keras.applications.inception_resnet_v2 import preprocess_input
from keras.backend import clear_session
import numpy as np
import glob
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.decomposition import PCA
from sklearn.preprocessing import scale
from pyclustertend import hopkins, vat, ivat
from sklearn.cluster import KMeans, DBSCAN, Birch
from yellowbrick.cluster import KElbowVisualizer, SilhouetteVisualizer, InterclusterDistance
from sklearn.metrics.cluster import adjusted_rand_score
from sklearn.neighbors import NearestNeighbors
from sklearn.metrics.cluster import silhouette_score
import string
import random

class Model():
    def __init__(self,files_list,number_of_clusters):
        self.files_list = files_list 
        self.number_of_clusters = number_of_clusters
    
    def preprocessing_images_and_model_loading(self):
        self.preprocessed_images = dict() 
        for i in self.files_list:
            try:
                img_path = i
                img = image.load_img(img_path, target_size=(299, 299)) # loading image to PIL and resizing to (299x299)
                img_data = image.img_to_array(img) # transformin PIL image to numpy array and adding channels there
                img_data = np.expand_dims(img_data, axis=0) # transforming numpy array to tensor style - it implies new shape: number_of_images x width x height x channels
                img_data = preprocess_input(img_data) # subtracts the mean RGB channels of the ImageNet dataset and other adequations for model
                self.preprocessed_images.update({i:img_data}) # adding img_data to dictionary for preprocessed images
            except:
                print(f"Fatal error for {i} image")
        clear_session()
        self.model_cnn = InceptionResNetV2(weights='imagenet', include_top=False, classes=1000) #loading pre-trained model from Keras library without top layer

    def model_application(self):
        self.extracted_features = dict() # dictionary for extracted features for each image
        for i,j in self.preprocessed_images.items():
            preds_features = np.array(self.model_cnn.predict(j)) # making prediction using InceptionResNetV2 model and saving it to numpy array
            self.extracted_features.update({i:preds_features.flatten()}) # collapsing array into one dimension
        df = pd.DataFrame.from_dict(self.extracted_features,orient="index") # creating Data Frame from dictionary - final dataset for clustering
        df = df.add_prefix('feature_') # adding prefix
        self.df = df
        self.data_frame_info = df.info()

    def id_generator(self, size=6, chars=string.ascii_uppercase + string.digits): 
        return ''.join(random.choice(chars) for _ in range(size))

    def pca_plot(self):
        pca = PCA(n_components=2) #creating pca object of PCA class
        principalComponents = pca.fit_transform(self.df) #fiting and transforming data by pca
        df_pca = pd.DataFrame(principalComponents,columns=["pc1","pc2"]) #creating useful dataset
        sns.set_style("darkgrid")
        plt.figure(figsize=(10,10))
        plot = sns.scatterplot(df_pca.pc1,df_pca.pc2,s=50)
        plot.axes.set_title('PCA - dataset visualization',fontsize=20)
        plot.set_xlabel("Component 1",fontsize=15)
        plot.set_ylabel("Component 2",fontsize=15)
        foo_name = "images/output/" + self.id_generator(30) + '.png'
        self.pca_name = foo_name
        plt.savefig(foo_name)
        # plt.show()

    def sillhouette_plot(self):
        kmeans = KMeans(n_clusters=self.number_of_clusters)
        plt.rcParams['figure.figsize'] = [10, 5]
        visualizer = SilhouetteVisualizer(kmeans, colors='yellowbrick')
        visualizer.fit(self.df)
        foo_name = "images/output/" + self.id_generator(30) + '.png'
        self.sillhouette_name = foo_name
        plt.title(f'Sillhouette plot based on Kmeans')
        visualizer.show(outpath=foo_name)

    def birch_model_and_plot(self):
        birch1 = Birch(n_clusters=self.number_of_clusters, branching_factor = 50, threshold=0.5)
        pca = PCA(n_components=2) # pca object
        principalComponents = pca.fit_transform(self.df) #fitting dataframe to PCA
        df_pca = pd.DataFrame(principalComponents,columns=["pc1","pc2"])
        labels = birch1.fit_predict(self.df) #obtaining labels from model which was passed to the function
        df_pca["cluster"] = labels #assignment of labels to nice pca dataframe
        title = "Birch " + str(self.number_of_clusters) + "clusters"
        cmap = sns.cubehelix_palette(dark=.3, light=.8, as_cmap=True)
        sns.set_style("darkgrid")
        plt.figure(figsize=(10,10))
        plot = sns.scatterplot(df_pca.pc1,df_pca.pc2,df_pca["cluster"],s=50, palette="Set2",legend='full') #ploting results taking into account class of the image distinction
        plot.axes.set_title(f'{title}',fontsize=20)
        plot.set_xlabel("Component 1",fontsize=15)
        plot.set_ylabel("Component 2",fontsize=15)
        plot.legend(fontsize='x-large', title_fontsize='20')
        foo_name = "images/output/" + self.id_generator(30) + '.png'
        self.birch_name = foo_name
        plt.savefig(foo_name)
        # plt.show()
        return labels