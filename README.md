# Build the tagged sentences

wget https://github.com/datquocnguyen/RDRPOSTagger/archive/master.zip -O RDRPOSTagger.zip
unzip RDRPOSTagger.zip
TAGGERDIR=$(pwd)"/RDRPOSTagger-master/pSCRDRtagger"

wget http://www.manythings.org/anki/spa-eng.zip
unzip spa-eng.zip
cut -f 2 spa.txt | sed -e "s/[[:punct:]]\+//g" > spa-clean.txt

WDIR=$(pwd) && cd $TAGGERDIR && python3 RDRPOSTagger.py tag ../Models/MORPH/Spanish.RDR ../Models/MORPH/Spanish.DICT $WDIR/spa-clean.txt && cd $WDIR

python3 build_sentences.py spa.txt spa-clean.txt.TAGGED > spanish_sentences/spa-tagged.txt


# Get the lemma data
cd spanish_lemmas
https://github.com/ChatScript/ChatScript/blob/master/DICT/SPANISH/


# Get the anki resources
mkdir deck
cd deck
download deck from https://ankiweb.net/shared/info/2134488481
python3 ../unpack_deck.py

# make any manual adjustments to spanish_5000.csv
python3 ../build_anki.py
