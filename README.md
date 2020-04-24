# Build the tagged sentences

mkdir treetagger
cd treetagger

wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tree-tagger-linux-3.2.2.tar.gz
wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish.par.gz
#wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/spanish-chunker.par.gz
#wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/tagger-scripts.tar.gz
wget https://cis.uni-muenchen.de/~schmid/tools/TreeTagger/data/install-tagger.sh

bash ./install-tagger.sh

wget http://www.manythings.org/anki/spa-eng.zip
unzip spa-eng.zip

pip3 install treetaggerwrapper
python3 build_sentences.py spa.txt > spanish_sentences/spa-tagged.txt


# Generate es-en.txt
# Generate synonyms.txt

run ./build.sh in spanish_words
