# Project Mercurius 🧠
**A Graph analysis-based EEG classifier for the early detection of Parkinsons Disease.**

| Name | Github Handle |
| --- | --- |
| Sébastien Pierret | @SebasPie |
| Béla Bernasconi | @B.Bernasconi |
| Andrés Santiago Martínez Hernández | @SantiagoMartinezHernandez |
| Ali Abdel Ghaffar | @AliAgh123 |

_Mercurius is the roman god of movement_

### 1. Project description

Codename project Mercurius, is an application of Graph Analysis and is usage into a GNN Classifier for the early detection of the Parkinsons Disease (PD). As part of the Social Media Analytics course.

The work will comprise a combination of deep graph analysis and the implementation of the gathered knowledge of a classifier based on EEG signals as input.

### 2. Dataset and technologies

The [Rest eyes open - Parkinsons Disease 64-Channel EEG](https://www.kaggle.com/datasets/anthonyylee/rest-eyes-open-parkinsons-disease-64-channel-eeg/code) from [Anjum et. al. 2020](https://www.prd-journal.com/article/S1353-8020(20)30667-2/abstract) is a 64-channel BrainVision EEG of 100x Parkinsons and 49x controls dataset of implementing a traditional test in the EEG field named the "rest eyes open" experiment.

Previous efforts towards using this type of datasets towards building accessible ML/DL classifiers for the early detection of PD have shown progress by building simple regression clasifiers but they lack depth in dimensionality and the complex interactions that can be captured by EEG. 

This project comprises the use of `NetworkX` and `Numpy` for the generation of EEG-based graphs that then will be analyzed with Graph analysis tools to understand the key communities, centrality and Pearson correlation to extract clear insights of the most relevant EEG features. Then a GNN model will be build using `PyTorch` to create a classifier ready to be tested on the clinical landscape.

### 3. Contributions of each member

All areas will be supervised by each member; however the following pairing and tasks is proposed:

| Task | Member |
| --- | --- |
| Graph generation | Sebastian, Béla |
| Graph Analysis | Ali , Santiago |
| GNN Architecture proposal | Santiago, Sebas |
| GNN Train and test | Béla, Ali |
| GNN Analysis and validation | All members |

### 4. Analytical task

The analytical task can be splitted into two core steps:

1. *Graph generation:* Adjancency matrices will be built using Pearson Correlation on each patient to have multiple graphs where the nodes are the electrodes and the edges are the Pearson correlation between them.  Based on this graphs, we will increase the complexity by building higher level graphs based on these "first level" graphs by comparing them based on graph simmilarity. So the new nodes are each one of the patients and the edges are the simmilarity between their corresponding graphs.

2. *Graph analysis:*  Centrality measures and community analysis will be extensively used to understand the "second layer" complexity of the graphs and detect comunities where we expect to find:

- Early classification of PD vs control
- The generation of comunities within PD based on similarity

We will then take this PD comunities and study the "first layer" graphs to find the most important EEG features (electrodes) to take them into account in the next step.

3. *Graph architecture proposal:* based on the most interesting features, a Py-torch GNN build based on the first layer graphs will be deployed and tested in a traditional 80/20 fashion.  We will then test f1 scores and AUC to study the behavior of the model and tune it to prevent overfitting and improve classification power.
