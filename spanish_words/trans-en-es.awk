# gawk script to create a Language-English dictionary
# from the Foreign-Language sections of en.wiktionary.org
# Version: 20200325
#
# (c) 2011-2020 by Matthias Buchmeier
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#
# TODO:
# Pronunciation and etymology sections inside POS and before definition lines?
## This is not compatible with #-ennumerated lines other than on definition lines
# hash-numbering inside etymology and synonyms sections; is this allowed?
# include participles?
# proper treatment of {{indtr|
# include synonyms and antonyms (syn and ant template)
# include usage examples?
# {{taxon|
# implement [[Wiktionary:Templates_with_current_language_parameter]]
# Command-line options:
########################
#  required gawk command-line switches:
#
#    name of the language to be extracted
#    -v LANG="language" 
#
#    iso-code of the language to be extracted
#    -v ISO="iso-code"
#
#  optional gawk command-line switches:
#
#    remove wiki-links and wiki-style bolding, italicizing:
#    -v REMOVE_WIKILINKS="y"
#
#########################

BEGIN {
#########################
# User defined variables:
#########################
# English names of the target language
# supported languages at the moment:
# Italian, French, Spanish, Finnish, Portuguese, German, Latin, Dutch, Polish, Russian, Serbo-Croatian
# phony target languages for dictionaries with inflected forms: 
# Italian_with_forms, French_with_forms, Spanish_with_forms, English_with_forms (monolingual English)
# default language and iso-code:
lang = "Spanish";
iso = "es"
#
# command line parsing:
#############################
if(LANG != "") lang = LANG;
if(ISO != "") iso = ISO;
# enable IPA pronunciation
enable_ipa = 0;
if(ENABLE_IPA == "y") enable_ipa = 1
#
if(REMOVE_WIKILINKS == "y") remove_wikilinks = 1;
else remove_wikilinks = 0;
#
#
# default options if not set in language configuration below
rm_headless_pos = 0;
has_neuter = 0;
nounhead = "\\{\\{head\\|"iso"\\|noun";
verbhead = "XXXXXX";
rmtemplate = "XXXXXX";
exclude_POS = "XXXXXX";
exclude_defn = "\\{\\{(rfdef|rftrans|defn|misspelling of|archaic form of)\\|";
#
# debug output filename:
fixme = "FIXME-"lang".txt";
#
###########################################
# language specific configuration: 
###########################################
#
# configuration for the Spanish-English dictionary
if(lang == "Spanish") {
#
# iso-code of the language as used in the templates
iso = "es";
#
# set has_neuter to 1 if the language has neuter gender, otherwise 0
## has_neuter=1 will switch the tag for nouns with missing gender to {noun} rather than {n}
has_neuter = 0;
#
# There are a couple of options to filter out undesired content:
##################################################################
#
# a regular expression (regexp) excluding the entire current part-of-speech (POS) subsection when matched
# this regexp should typically contain headline-templates of non-lemma (form of) entries
exclude_POS = "\\{\\{es-adj[^\\}]*\\|(m|masculine)\\=|\\{\\{(head\\|es\\|(participle form|past participle form|present participle|noun plural form|(noun|adjective|verb) form|misspelling|obsolete)|es-adj-form|es-verb-form)(\\||\\})";
#
# a regexp to exclude the whole matched definition line
# this typically contains form of definition-line templates etc.
exclude_defn = "\\{\\{(es-verb form of|rfdef|defn|form of|inflection of|archaic form of|misspelling of|es-compound of|infl of)(\\||\\})";
#
# language specific templates to be removed from the output lines
# the rest of definition line is kept
# regexp must match the TEMPLATE-NAME!! not the template
 rmtemplate = "XXXXXX";
#
# This option (rm_headless_pos=1) discards entire POS sections without head-line template
# which contain '''PAGENAME''' as headline
# it is the only way to filter form-of entries without headline template and definition-line form-of templates
rm_headless_pos = 0;

#
# Regexps matching headline templates
# used to set the gender, transitivity etc.
####################################################################
#
# noun headline
nounhead = "\\{\\{head\\|es\\|(noun|proper noun)\\||\\{\\{es-noun\\||\\{\\{es-proper noun\\|";
#
# verb headline
verbhead = "\\{\\{es-verb[\\|\\}]|\\{\\{head\\|es\\|verb[\\|\\}]";
#
# Options to add pronunciation
enable_ipa = 0;
# default regex matching IPA-pronunciation line 
#defipa = "\\\\{\\{es-IPA\\|";
# alternative IPA regex
#altipa = "\\{\\{IPA\\|";
	
}
#
#
if(lang == "Portuguese") {
iso = "pt";
exclude_POS = "\\{\\{(head\\|pt\\|(past participle|verb|adjective) form)(\\||\\})"
exclude_defn = "\\{\\{(pt-verb form of|pt-verb-form-of|conjugation of|misspelling of|pt-noun form of|pt-adj form of|feminine past participle of|feminine plural past participle of|masculine plural of|feminine plural of|inflection of|pt-ordinal form|pt-adv form of|plural form of|pt-article form of|masculine plural past participle of|pt-cardinal form of|pt-apocopic-verb|rfdef|plural of|form of|archaic form of)\\|";
nounhead = "\\{\\{head\\|pt\\|(noun|proper noun)|\\{\\{pt-noun\\||\\{\\{pt-proper noun\\|";
verbhead = "\\{\\{pt-verb[\\|\\}]|\\{\\{head\\|pt\\|verb[\\|\\}]";
rm_headless_pos = 1;
has_neuter = 0;
#
# Options to add pronunciation
enable_ipa = 1;
# default regex matching IPA-pronunciation line 
defipa = "\\{\\{a\\|(PT|Portugal).*\\{\\{IPA\\|";
# alternative IPA regex
altipa = "\\{\\{IPA\\|";
}
#
#
if(lang == "Italian") {
iso = "it";
exclude_POS = "\\{head\\|it\\|[^\\:\\|]* form[s]*[\\|\\}]|\\{\\{(head\\|it\\|(misspelling|obsolete|plural|g=)|it-pp|it-adj-form)[\\|\\}]|\\{\\{head\\|it\\}";
exclude_defn = "Compound of|\\{\\{(rfdef|defn|misspelling of|uncommon spelling of|archaic form of|conjugation of|inflection of|form of|feminine (singular|plural) past participle of|masculine plural past participle of|feminine past participle of|(masculine|feminine) plural of|it-adj form of|gerund of|plural of)(\\||\\})";
verbhead = "\\{\\{it-verb[\\|\\}]|\\{\\{head\\|it\\|verb[\\|\\}]";
nounhead = "\\{\\{head\\|it\\|noun|\\{\\{it-noun\\||\\{\\{it-noun-pl\\||\\{\\{it-plural noun\\|";
rm_headless_pos = 1;
has_neuter = 0;
#
enable_ipa = 1;
enable_lua = 1;
# default regex matching IPA-pronunciation line 
defipa = "\\{\\{IPA\\|";
# alternative IPA regex
altipa = "\\{\\{it-stress\\||\\{\\{it-IPA\\|";
}
#
if(lang == "French") {
iso = "fr";
exclude_POS = "\\{\\{head\\|fr\\|[^\\|]* form[s]*[\\|\\}]|\\{\\{head\\|fr\\|(misspelling|obsolete|plural|present participle|g=)|\\{\\{(misspelling of|fr-pp|fr-verb-form|fr-verb form|fr-adj-form|fr-past participle)(\\||\\})|\\{\\{head\\|fr\\}";
exclude_defn = "\\{\\{past participle of\\||Compound of|masculine plural past participle of|present participle of|feminine plural past participle of|masculine plural of|conjugation of|inflection of|plural of|feminine plural of|feminine past participle of|plural past participle of|\\{\\{(rfdef|defn|plural of|form of|inflection of|archaic form of)(\\||\\})";
verbhead = "\\{\\{fr-verb[\\|\\}]|\\{\\{head\\|fr\\|verb[\\|\\}]";
nounhead = "\\{\\{head\\|fr\\|(noun|proper noun)(\\||\\})|\\{\\{fr-noun\\||\\{\\{fr-proper noun(\\||\\})";
rm_headless_pos = 0;
has_neuter = 0;
}
#
if(lang == "Finnish") {
iso = "fi";
exclude_POS = "\\{\\{head\\|fi\\|(noun|adjective|verb|proper noun) form|\\{\\{head\\|fi\\|(misspelling|obsolete)|\\{\\{misspelling of\\||\\{\\{head\\|fi\\}|\\{\\{head\\|fi\\|infinitive(\\||\\})";
exclude_defn = "\\{\\{(fi-form of|fi-participle of|infinitive of|inflected form of|agent noun of|fi-verb form of|defn|rfdef|nominative plural of|rftrans|plural of|form of|inflection of|archaic form of)(\\||\\})";
rm_headless_pos = 0;
has_neuter = 0;
}
#
if(lang == "Latin") {
iso = "la";
exclude_POS = "\\{\\{la-(verb|part|noun|proper noun|adj|gerund|num)-form(\\||\\})";
exclude_defn = "\\{\\{(conjugation of|inflection of|(genitive|nominative|vocative|accusative) (singular|plural) of|misspelling of|defn|combining form of|inflected form of|rfdef|rftrans|plural of|archaic form of)\\|";
has_neuter = 1;
nounhead = "\\{\\{head\\|la\\|(noun|proper noun)(\\||\\})|\\{\\{la-noun\\||\\{\\{la-proper noun(\\||\\})";
rm_headless_pos = 1;
}
#
if(lang == "German") {
iso = "de";
exclude_POS = "\\{\\{head\\|de\\|(verb|noun|proper noun|adjective) form(\\||\\})";
exclude_defn = "\\{\\{(conjugation of|inflection of|(genitive|nominative|vocative|accusative) (singular|plural) of|de-verb form of|misspelling of|defn|combining form of|inflected form of|rfdef|rftrans|plural of|archaic form of|de-inflected form of|form of|de-form-adj|past tense of|de-form-noun|genitive of|dative plural of|de-umlautless spelling of|accusative of|dative of|dative singular of|de-zu-infinitive of|de-du contraction|obsolete typography of|present participle of|noun form of|verb form of)(\\||\\})";
has_neuter = 1;
nounhead = "\\{\\{head\\|de\\|(noun|proper noun)\\||\\{\\{de-noun\\||\\{\\{de-proper noun\\||\\{\\{de-plural noun\\|";
rmtemplate = "gerund of";
# almost no entries without headline template (as of 2017 06)
rm_headless_pos = 0;
}
#
if(lang == "Dutch") {
iso = "nl";
exclude_POS = "\\{\\{(nl-adj-form|nl-verb-form|head\\|nl\\|noun plural form)(\\||\\})";
exclude_defn = "\\{\\{(nl-noun form of|nl-adj form of|nl-verb form of|misspelling of|form of|inflection of|archaic form of)(\\||\\})";
nounhead = "\\{\\{head\\|nl\\|(noun|proper noun)\\||\\{\\{nl-noun\\||\\{\\{nl-proper noun\\|";
has_neuter = 1;
rm_headless_pos = 1;
rmtemplate = "g2";
}
#
if(lang == "Polish") {
iso = "pl";
exclude_POS = "\\{\\{(pl-verb-form|pl-noun-form|head\\|pl\\|(verb|noun|proper noun|adjective|numeral|participle|noun plural|comparative adjective|superlative adjective) form|pl-participle)(\\||\\})";
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname)(\\||\\})";
nounhead = "\\{\\{head\\|pl\\|(noun|proper noun)\\||\\{\\{pl-noun\\||\\{\\{pl-proper noun\\|";
verbhead = "\\{\\{pl-verb[\\|\\}]|\\{\\{head\\|pl\\|verb[\\|\\}]";
has_neuter = 1;
rm_headless_pos = 1;
rmtemplate = "g2";
}
#
if(lang == "Russian") {
iso = "ru";
exclude_POS = "\\{\\{(head\\|ru\\|(past participle|verb|adjective|noun plural|noun|proper noun|participle|numeral) form|ru-noun form|head\\|ru\\|participle)(\\||\\})"
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname|passive of|passive form of|patronymic|ru-pre-reform|infl of)(\\||\\})";
nounhead = "\\{\\{(head\\|ru\\|(noun|proper noun)|ru-noun|ru-noun[+]|ru-noun-alt-ё|ru-proper noun|ru-proper noun[+]|ru-proper noun-alt-ё)(\\||\\})";
verbhead = "\\{\\{(head\\|ru\\|verb|ru-verb)(\\||\\})";
rmtemplate = "Русская грамматика|ru-etym initialism of";
rm_headless_pos = 1;
has_neuter = 1;
enable_ipa = 0;
}
#
if(lang == "Serbo-Croatian") {
iso = "sh";
exclude_POS = "\\{\\{(head\\|sh\\|(past participle|verb|adjective|noun plural|noun|proper noun|participle|numeral) form|sh-noun form|sh-noun-form|sh-proper-noun-form|sh-verb-form|sh-pronoun-form|sh-participle|head\\|sh\\|participle)(\\||\\})"
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname|passive of|passive form of|patronymic|sh-form-noun|sh-verb form of|definite of|past passive participle of|noun form of|verb form of)(\\||\\})";
nounhead = "\\{\\{(head\\|sh\\|(noun|proper noun)|sh-noun|sh-proper noun)(\\||\\})";
verbhead = "\\{\\{(head\\|sh\\|verb|sh-verb)(\\||\\})";
rm_headless_pos = 1;
has_neuter = 1;
enable_ipa = 0;
}
#
if(lang == "Czech") {
iso = "cs";
exclude_POS = "\\{\\{(head\\|cs\\|(past participle|verb|adjective|noun plural|noun|proper noun|participle|numeral) form|cs-noun form|cs-verb form|cs-verb-form|head\\|cs\\|participle)(\\||\\})"
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname|passive of|passive form of|patronymic|sh-form-noun|definite of|past passive participle of|infl of)(\\||\\})";
nounhead = "\\{\\{(head\\|cs\\|(noun|proper noun)|cs-noun|cs-proper noun)(\\||\\})";
verbhead = "\\{\\{(head\\|cs\\|verb|cs-verb)(\\||\\})";
rm_headless_pos = 1;
has_neuter = 1;
enable_ipa = 0;
}
#
if(lang == "Macedonian") {
iso = "mk";
exclude_POS = "\\{\\{(head\\|mk\\|(past participle|verb|adjective|noun plural|noun|proper noun|participle|numeral) form)(\\||\\})"
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname|passive of|passive form of|patronymic|definite of|past passive participle of|plural indefinite of|hu-participle)(\\||\\})";
nounhead = "\\{\\{(head\\|mk\\|(noun|proper noun)|mk-noun|mk-proper noun)(\\||\\})";
verbhead = "\\{\\{(head\\|mk\\|verb|mk-verb)(\\||\\})";
rm_headless_pos = 1;
has_neuter = 1;
enable_ipa = 0;
}
#
if(lang == "Hungarian") {
iso = "hu";
exclude_POS = "\\{\\{(head\\|hu\\|(past participle|verb|adjective|noun plural|noun|proper noun|participle|numeral) form)(\\||\\})"
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname|passive of|passive form of|patronymic|definite of|past passive participle of|plural indefinite of|hu-inflection of|hu-participle)(\\||\\})";
verbhead = "\\{\\{(head\\|hu\\|verb|hu-verb)(\\||\\})";
rm_headless_pos = 1;
has_neuter = 0;
enable_ipa = 0;
}
#
if(lang == "Greek") {
iso = "el";
exclude_POS = "\\{\\{(head\\|el\\|(past participle|verb|adjective|noun plural|noun|proper noun|participle|numeral) form)(\\||\\})"
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname|passive of|passive form of|patronymic|definite of|past passive participle of|el-form-of-nounadj|Katharevousa form of|el-verb form of|el-form-of-verb|katharevousa|el-form-of-adv|polytonic form of|el-polytonic form of|morse code for|el-form-of-pronoun|el-comp-form-of|el-participle of|monotonic form of|el-Katharevousa form of|el-poly-of)(\\||\\})";
verbhead = "\\{\\{(head\\|el\\|verb|el-verb)(\\||\\})";
nounhead = "\\{\\{(head\\|el\\|(noun|proper noun)|el-noun|el-noun-proper)(\\||\\})";
rm_headless_pos = 1;
has_neuter = y;
enable_ipa = 0;
}
#
if(lang == "Vietnamese") {
iso = "vi";
exclude_POS = "\\{\\{(head\\|vi\\|(past participle|verb|adjective|noun plural|noun|proper noun|participle|numeral) form)(\\||\\})"
exclude_defn = "\\{\\{(misspelling of|form of|inflection of|archaic form of|surname|past passive participle of|defn|han tu form of|Nom form of|nomof|sino-vietnamese reading of|vi-etym-sino)(\\||\\})";
verbhead = "\\{\\{(head\\|vi\\|verb|vi-verb)(\\||\\})";
rm_headless_pos = 1;
has_neuter = n;
enable_ipa = 0;
}
#
if(lang == "Mandarin") {
iso = "cmn";
lang = "(Chinese|Mandarin)";
rm_headless_pos = 0;
has_neuter = n;
enable_ipa = 1;
defipa = "\\{\\{zh-pron";
altipa = "XXXXXXX";
}
#
if(lang == "Danish") {
iso = "da";
#exclude_POS = "XXXXX";
exclude_POS = "\\{\\{(head\\|da\\|(noun|verb|adjective) form)(\\||\\})"
exclude_defn = "\\{\\{(defn|superlative predicative of|superlative attributive of|singular indefinite of|da-e-form of|definite plural of|inflection of)(\\||\\})";
nounhead = "\\{\\{head\\|da\\|(noun|proper noun)\\||\\{\\{da-noun\\||\\{\\{da-noun-pl\\|";
verbhead = "\\{\\{(head\\|da\\|verb|da-verb)(\\||\\})";
has_neuter = 1;
rm_headless_pos = 0;
rmtemplate = "XXXXX";
}
#
# Configuration for dictionaries containing all inflected forms
#
if(lang == "Italian_with_forms") {
iso = "it";
lang = "Italian";
verbhead = "\\{\\{it-verb[\\|\\}]|\\{\\{head\\|it\\|verb[\\|\\}]";
nounhead = "\\{\\{head\\|it\\|noun|\\{\\{it-noun\\||\\{\\{it-noun-pl\\||\\{\\{it-plural noun\\|";
rm_headless_pos = 0;
has_neuter = 0;
#
enable_ipa = 1;
enable_lua = 1;
# default regex matching IPA-pronunciation line 
defipa = "\\{\\{IPA\\|";
# alternative IPA regex
altipa = "\\{\\{it-stress\\||\\{\\{it-IPA\\|";
}
#
if(lang == "French_with_forms") {
iso = "fr";
lang = "French";
verbhead = "\\{\\{fr-verb[\\|\\}]|\\{\\{head\\|fr\\|verb[\\|\\}]";
nounhead = "\\{\\{head\\|fr\\|(noun|proper noun)(\\||\\})|\\{\\{fr-noun\\||\\{\\{fr-proper noun(\\||\\})";
rm_headless_pos = 0;
has_neuter = 0;
}
#
if(lang == "Spanish_with_forms") {
iso = "es";
lang = "Spanish";
verbhead = "\\{\\{es-verb[\\|\\}]|\\{\\{head\\|es\\|verb[\\|\\}]";
nounhead = "\\{\\{head\\|es\\|(noun|proper noun)(\\||\\})|\\{\\{es-noun\\||\\{\\{es-proper noun(\\||\\})";
rm_headless_pos = 0;
has_neuter = 0;
}
#
if(lang == "Portuguese_with_forms") {
iso = "pt";
lang = "Portuguese";
verbhead = "\\{\\{pt-verb[\\|\\}]|\\{\\{head\\|pt\\|verb[\\|\\}]";
nounhead = "\\{\\{(head\\|pt\\|(noun|proper noun)|pt-noun|pt-proper noun|pt-noun-form)(\\||\\})";
rm_headless_pos = 0;
has_neuter = 0;
enable_ipa = 1;
# default IPA regexp
defipa = "\\{\\{a\\|(PT|Portugal).*\\{\\{IPA\\|";
# alternative IPA regexp
altipa = "\\{\\{IPA\\|";
}
#
if(lang=="German_with_forms") {
iso = "de";
lang = "German";
nounhead = "\\{\\{head\\|de\\|(noun|proper noun)\\||\\{\\{de-noun\\||\\{\\{de-proper noun\\||\\{\\{de-plural noun\\|";
rm_headless_pos = 0;
has_neuter = 1;
}
#
if(lang == "Latin_with_forms") {
iso = "la";
lang = "Latin";
has_neuter = 1;
nounhead = "\\{\\{head\\|la\\|(noun|proper noun)(\\||\\})|\\{\\{la-noun\\||\\{\\{la-proper noun(\\||\\})";
rm_headless_pos = 0;
}
#
if(lang=="English_with_forms") {
iso = "en";
lang = "English";
# template der: most likely a line from the etymology section/
exclude_defn = "\\{\\{der\\||\\{\\{translation only\\|"
has_neuter = 0;
nounhead = "XXXXXXXXXX";
rm_headless_pos = 0;
enable_ipa = 1;
# default IPA regexp
defipa = "\\{\\{a\\|(US|GenAm).*\\{\\{IPA\\|";
# alternative IPA regexp
altipa = "\\{\\{IPA\\|";
#
}
#
#
# initialization of variables used for parsing
#
# set to 0/1 if outside/inside language section 
langsect = 0; 
# variable holding POS (part of speech) information 
# pos=="-" means the current POS is a non-lemma form to be excluded from the dictionary 
pos = "";
# variables holding additional grammatical information as gender, plural/singular etc.
# from headline-templates
gend = "";
# from definition-lines
gend2 = "";
# variable holding page title
title = ""; 
# headline=1 inside headlines =0 elsewhere
headline = 0;
#
# inside Pronunciation section? 0/1
pron = 0;
# default IPA pronunciation
ipa1 = "";
# alternative IPA pronunciation
ipa2 = "";
#
# language dependent regular expressions
# regexp matching language section header
langhead="[=][=][ ]*" lang "[ ]*[=][=]";
warnmissing="[[][[]Category:"lang" (nouns|adjectives|verbs)[]][]]";

##########################
# mapping of shortcuts:
##########################
#
# mapping of iso-codes to language-names (incomplete)
isocodes="en|grc|la|es|ru|pt|LL.|it|gem|cel|ga|eu|de|fr|sv|ar|cel-gae|roa-opt|da|no|nl|nds-de|non|sla|el|cy|enm|ang|he|fro|ga|bg|hbo|sa|is|zh|ko|haw|gd|hi|fo|sco|kw|chn|xno|fa|gsw|frk|ml|ta|ja";
languages="English|Ancient Greek|Latin|Spanish|Russian|Portuguese|Late Latin|Italian|Germanic|Celtic|Irish|Basque|German|French|Swedish|Arabic|Goidelic|Old Portuguese|Danish|Norwegian|Dutch|Low German|Old Norse|Slavic|Greek|Welsh|Middle English|Old English|Hebrew|Old French|Gaelic|Bulgarian|Biblical Hebrew|Sanskrit|Islandic|Chinese|Korean|Hawaiian|Scottish Gaelic|Hindi|Faroese|Scots|Cornish|Chinook Jargon|Anglo-Norman|Persian|Alemannic|Frankish|Malayalam|Tamil|Japanese";
# write isocodes and language-names into array
n1=split(isocodes,iso_array,"|");
n2=split(languages,languages_array,"|");
if(n1 != n2) print "#WARNING: badly formatted language strings" >fixme;
for(i=1;i<=n1;i++) { language_names[iso_array[i]] = languages_array[i];
#print iso_array[i]" "language_names[iso_array[i]];
}
#
# mapping of grammar shortcuts used in form of templates:
# incomplete and possible conflicting among templates
# TODO: all shortcuts from Module:form of/data
# shortcuts:
shortcuts="1|first|first person|2|second|second person|3|third|third person|0|imp|impers|s|sg|sing|p|pl|d|col|m|f|mf|m-f|n|c|pres|past|fut|futr|prog|pret|preterit|perf|imp|impf|imperf|plup|pluperf|phis|imp|impr|ind|indc|indic|sub|subj|cond|dat|acc|actv|act|part|par|ger|gerundio|gerundive|adv|inf|y|n|aff|+|neg|-|onlym|onlyf|a|ª|as|ªs|os|ºs|pr|pp|i|g|v|k1|k2|gen|nom|voc|abl|pasv|pass|sup|loc|ptcp|def|indef|aug|dim|super|ins|an|pers|mix|str|wk|comd|supd|poss|adj|12|2s|3s|3p|1p|2p|sim|obs";
# corresponding replacements:
replacement="first-person|first-person|first-person|second-person|second-person|second-person|third-person|third-person|third-person|impersonal|impersonal|impersonal|singular|singular|singular|plural|plural|dual|collective|masculine|feminine|masculine and feminine|masculine and feminine|neuter|common|present|past|future|future|progressive|preterite|preterite|perfect|imperfect|imperfect|imperfect|pluperfect|pluperfect|past historic|imperative|imperative|indicative|indicative|indicative|subjunctive|subjunctive|conditional|dative|accusative|active|active|participle|participle|gerund|gerund|gerund|adverbial|infinitive|yes|no|affirmative|affirmative|negative|negative|only masculine|only feminine|feminine singular|feminine singular|feminine plural|feminine plural|masculine plural|masculine plural|present participle|past participle|imperative|present tense|past tense|subjunctive 1|subjunctive 2|genitive|nominative|vocative|ablative|passive|passive|supine|locative|participle|definite|indefinite|augmentative|diminutive|superlative|instrumental|animate|personal|mixed|strong|weak|comparative degree|superlative degree|possissive|adjectival|first/ and second-person|second-person singular|third-person singular|third-person plural|first-person plural|second-person plural|simple|obsolete";
# common strings which are no shortcuts:
non_replacement = ";|,|and|historic|of the|simple|[[past historic]]|indirect|form|object|past participle|personal infinitive|strong|weak|mixed|tense|/|adjectival|early|(impersonal)|I|II|archaic|weak form|intensified|superlative|strong|mute|nonvirile|virile|other|contemporary|personal|personal masculine|nonmasculine|anterior|personal and animate masculine|all-gender|all-case|all cases|comparative|alternative";
# add self reference and common non-shortcuts to avoid warnings:
shortcuts = shortcuts "|" non_replacement "|" replacement ;
replacement = replacement "|" non_replacement "|" replacement ;
# write replacement text into array
n1=split(shortcuts,sh_array,"|");
n2=split(replacement,rep_array,"|");
if(n1 != n2) print "#WARNING: badly formatted grammar shortcut strings" >fixme;
for(i=1;i<=n1;i++) {
	grep_text[sh_array[i]] = rep_array[i];
# 	print sh_array[i] " " grep_text[sh_array[i]];
}

# shortcuts for template names:(Italiot|Cretan|Maniot|Cypriot) dialect form of
shortcuts="altform|alt-form|altcaps|altspelling|altspell|alt-sp|synonym|abbreviation|clipping|abbreviation-old|altname|pf.|indeclinable|plural|de-inflected form of|pt-verb-form-of|de-form-adj|pt-apocopic-verb|de-form-noun|de-du contraction|de-umlautless spelling of|de-zu-infinitive of|synof|only-in|altspell|en-simple past of|en-third-person singular of|en-past of|en-comparative of|phrasal verb|en-superlative of|en-irregular plural of|en-archaic second-person singular of|pronunciation spelling|en-third person singular of|alt form of|en-archaic third-person singular of|fr-post-1990|obs-sp|abb|ru-abbrev of|ru-initialism of|ru-pre-reform|ru-acronym of|ru-alt-ё|dim of|onlyin|cs-imperfective form of|syn of|syn-of|altcase|cretan dialect form of|ao|io|clip|rareform|past participle|ellipse of|ellipsis|obssp|standspell|back-form|abbr of|alt sp|alt case|init of|obs sp|clip of|honor alt case|en-archaic second-person singular past of|stand sp|alt form|el-Italiot dialect form of|el-Cretan dialect form of|el-Maniot dialect form of|el-Cypriot dialect form of|la-praenominal abbreviation of|zh-original|zh-abbrev|zh-only|zh-used|zh-alt-form|zh-classifier|zh-short|zh-only used in|zh-used in|zh-erhua form of|zh-altterm|zh-also|pinread|pinof|zh-character component|zh-see|zh-misspelling|cmn-erhua form of|obs form";

replacement="alternative form of|alternative form of|alternative letter-case form of|alternative spelling of|alternative spelling of|alternative spelling of|synonym of|abbreviation of|clipping of|old abbreviation of|alternative name of|pf|indecl|p|inflected form of|verb form of|adjective form of|apocopic (used preceding the pronouns lo, la, los or las) form of|noun form of|Contraction of|nonstandard umlautless spelling of|zu-infinitive of|synonym of|only in|alternative spelling of|simple past of|third-person singular of|simple past tense and past participle of|comparative form of|A component in at least one phrasal verb:|superlative of|irregular plural of|archaic second-person singular of|pronunciation spelling of|third person singular of|alternative form of|archaic third-person singular of|post-1990 spelling of|obsolete spelling of|abbreviation of|abbreviation of|initialism of|pre-reform form of|acronym of|alternative form of|diminutive of|only used in|imperfective form of|synonym of|synonym of|alternative letter-case form of|Cretan dialect form of|abbreviation of|initialism of|clipping o|rare form of|past participle of|ellipsis of|ellipsis of|obsolete spelling of|standard spelling of|back formation from|abbreviation of|alternative spelling of|alternative case form of|initialism of|obsolete spelling of|clipping of|honorific alternative case of|archaic second-person singular past of|standard spelling of|alternative form of|Italiot dialect form of|Cretan dialect form of|Maniot dialect form of|Cypriot dialect form of|praenominal abbreviation of|original form of|abbreviation of|only used in|only used in|alternative form of|classifier for|abbreviation of|only used in|used in|erhua form of|alternative form of|⇒|pinyin reading of|pinyin reading of|the Chinese character component|see|misspelling of|Mandarin erhua form of|obsolete form of";

n1=split(shortcuts,sh_array,"|");
n2=split(replacement,rep_array,"|");
if(n1 != n2) print "#WARNING: badly formatted template-name shortcut strings" >fixme;
for(i=1;i<=n1;i++) {
	trep_text[sh_array[i]] = rep_array[i];
#	print sh_array[i] "::" trep_text[sh_array[i]];
}

# TODO: label shortcuts:
shortcuts="uds.|mostly|informal|brazil|portugal";
replacement="formal in Spain|chiefly|colloquial|Brazil|Portugal"
n1=split(shortcuts,sh_array,"|");
n2=split(replacement,rep_array,"|");
if(n1 != n2) print "#WARNING: badly formatted label shortcut strings" >fixme;
for(i=1;i<=n1;i++) { lrep_text[sh_array[i]] = rep_array[i];
#print sh_array[i] " " lrep_text[sh_array[i]];
	}
}
# end of BEGIN block
########################

########################
# function definitions:

function sc2txt(shortcut,    sc1,sc2) {
# replace shortcut with text
if(shortcut == "") return "";
if(match(shortcut, "//") !=0) {
#print "// detected in sc2txt, shortcut:" shortcut>fixme
sc1 = shortcut
sc2 = shortcut
gsub(/^.*\/\//, "", sc1)
gsub(/\/\/.*$/, "", sc2)
return sc2txt(sc1) " and " sc2txt(sc2);
}
if(shortcut in grep_text) return grep_text[shortcut];
else {	
	print  "#WARNING: unknown shortcut:\"" shortcut "\" on page:\"" title "\", line:" $0 >fixme;
	return shortcut;
}	
}

function iso2lang(isocode) {
# replace iso-code with language name
if(isocode == "") return "";
if(isocode in language_names) return language_names[isocode];
else {	
	print  "#WARNING: unknown iso-code:\"" isocode "\" on page:\"" title "\", line:" $0 >fixme;
	return isocode;
}	
}

function replace_template(tpar, n_unnamed,     outp, i, j, start)	{
# scans tpar and returns replacement string for the template
# tpar[0] is the template name
# tpar[1], ..., tpar[n_unnamed] are the unnamed parameters
# tpar["name1"], ...,  tpar["nameN"] are the named parameters with names name1, ..., nameN
outp = "";

# debug output
# for (j in tpar) print j, tpar[j];
# print tpar[0]; 
MAXGENDERS = 5;

# user-defined remove per language:
if(tpar[0] ~ rmtemplate) return "";

outp = "";
switch (tpar[0]) {

# qualifier
case "qfliteral":
outp = "literally: ";
	
case /^(qualifier|i|italbrac|ib|qual|q|a|qf)$/:
outp =  outp tpar[1];
for(i=2;i in tpar;i++){
	if(tpar[i] in lrep_text) tpar[i] = lrep_text[tpar[i]]; 
	outp = outp ", " tpar[i];
}
outp = linktotext(outp);
return "[" outp "]";

# gloss-template -> ({{1}})
case /^(gloss|sense|gl)$/:
outp = "(" tpar[1] ")";
return outp;

# l-templates
case /^(l|l-self|link|m|m[+]|mention|m-self|ll|l\/.*|alter)$/:
if(tpar[2] ~ /\[\[/) outp = tpar[2];
else {
		if((3 in tpar)&&(tpar[3]!="")) outp = "[[" tpar[2] "|" tpar[3] "]]";
		else outp = "[[" tpar[2] "]]";
}
if(("tr" in tpar)&&(tpar["tr"] != "-")) outp = outp " /" tpar["tr"] "/";
if(4 in tpar) outp = outp " (" tpar[4] ")";
if("gloss" in tpar) outp = outp " (" tpar["gloss"] ")";
return outp;

# lb-template
# TODO: senseid etc as first template
# TODO: join the code with term-label?
case /^(lb|label|lbl|indtr)$/:
j=1;
for(i=2;i in tpar;i++) {
if(pos=="v") {
	if(tpar[i] == "intransitive") { gend2 = (gend2 "i"); continue;}
	if(tpar[i] == "transitive") { gend2 = (gend2 "t"); continue;}
	if(tpar[i] == "ambitransitive") { gend2 = (gend2 "it"); continue;}
	if(tpar[i] == "reflexive") { gend2 = (gend2 "r"); continue;}
	if(tpar[i] == "pronominal") { gend2 = (gend2 "p"); continue;}
}
j++;
		if(j > 2) outp = outp ", ";
		if(tpar[i] in lrep_text) tpar[i] = lrep_text[tpar[i]]; 
		outp = outp tpar[i];
}
# cleanup ", _,", ", and," etc
gsub(/,[\ ]_,/, "", outp);
outp = gensub(/,[\ ](and|or)[,]*[\ ]/, " \\1 ", "g", outp);
gsub(/^(and|or)$/, "", outp);
gsub(/^(and|or),[\ ]/, "", outp);
gsub(/,[\ ](and|or)$/, "", outp);
gsub(/chiefly,/, "chiefly", outp);

# there might be labels on the headline
if((headline == 1)&&(pos=="v")) gend = gend gend2;
outp = linktotext(outp);
if(template_number == 1) {
	LHS_qualifier = LHS_qualifier outp; 
	return ""; 
}
if(j==1) outp = "";
	else outp = "[" outp "]";

return outp;

# labels on headline for entire pos
case /^(tlb|term-label|term-context|tcx)$/:
if(headline != 1) {
# print "#WARNING: term-label on definition-line, page: \"" title "\", line: \"" $0 "\"" >fixme;
return "";
}

if(tpar[0] ~  /^(tlb|term-label)$/) start =2;
	else start =1;
j=1;
for(i=start;i in tpar;i++) {
if(pos=="v") {
	if(tpar[i] == "intransitive") { gend = (gend "i"); continue;}
	if(tpar[i] == "transitive") { gend = (gend "t"); continue;}
	if(tpar[i] == "ambitransitive") { gend = (gend "it"); continue;}
	if(tpar[i] == "reflexive") { gend = (gend "r"); continue;}
	if(tpar[i] == "pronominal") { gend = (gend "p"); continue;}
}
j++;
		if(j > 2) outp = outp ", ";
		if(tpar[i] in lrep_text) tpar[i] = lrep_text[tpar[i]]; 
		outp = outp tpar[i];
}
outp = linktotext(outp);
# cleanup ", _,", ", and," etc
gsub(/,[\ ]_,/, "", outp);
outp = gensub(/,[\ ](and|or)[,]*[\ ]/, " \\1 ", "g", outp);
gsub(/^(and|or)$/, "", outp);

if(outp != "") {
if(term_label != "") term_label = term_label ", ";
term_label = term_label outp;
}
return "";


# templates to be deleted
# add know templates to get rid off "unknown template" warnings
case /^(attention|rfc-tbot|inv|rfr|rfscript|rftranslit|NNBS|RL|LR|\,|jump|rfv|rfex|rfgloss|attention|rfv-sense|defdate|gloss-stub|senseid|es-demonstrative-accent-usage|R[:].*|pos_n|rfdef|cite-web|cite|C|cite-book|rft-sense|cite|rfquote-sense|RFV-sense|rfc-sense|datedef|ISBN|topics|anchor|color panel|colour panel|colorbox|nowrap|pedialite|rfm-sense|cite-journal|cite book|wikipedia|rfc-def|rfd-sense|rfdate|attn|sense stub|c|categorize|cln|catlangname|question|rfinfl|cite web|top|wiki|cite news|rfd-redundant|rfexample|rfdatek|rfphoto|rfquotek|rfcite-sense|Cite book|example needed|quote-book|Cite news|rfusex|gbooks|examples-right|hot sense|-|refn|U:fr:1990 reform spelling|rfquote|EtymOnLine|rfclarify)$/:
template_number -= 1;
return "";

# get gender from the head-template:
case "head":
if(headline ==1) 
{
#for(i in tpar) print i, tpar[i];
if("g" in tpar) gend = gend sob tpar["g"] scb;
# g1 is in code but not documented!
if("g1" in tpar) gend = gend sob tpar["g1"] scb;
if("g2" in tpar) gend = gend sob tpar["g2"] scb;
if("g3" in tpar) gend = gend sob tpar["g3"] scb;
if("fg1" in tpar) gend = gend sob tpar["fg1"] scb;
if("fg2" in tpar) gend = gend sob tpar["fg2"] scb;
if("fg3" in tpar) gend = gend sob tpar["fg3"] scb;

# print "gender info on head-template: \"" gend "\""
}
else print "#WARNING: misplaced head-template, page: \"" title "\", line: \"" $0 "\"" >fixme;
return "";


# the g-template
case "g":
outp = "";
for(i=1;i in tpar;i++)	outp = outp sob tpar[i] scb;
if(headline == 0) return outp;
	else {
		gend = gend outp;
		return "";
}

# obsolete term, vern etc {{1}} -> [[1]]
case /^(term|vern|specieslink)$/:
return "[[" tpar[1] "]]";

# show capitalised link
# TODO link to uncapitalized
case "1":
return "[[" toupper(substr(tpar[1],1,1)) substr(tpar[1],2) "]]";

# template-name [[{{1}}]], {{1}} or template-name [[{{2}}]], {{2}} (if lang named parameter is not present then the first unnamed parameter is the language iso-code)
case /^(altform|alt-form|altcaps|altspelling|alt-sp|synonym|abbreviation|clipping|altname|synof|only-in|altspell|phrasal verb|pronunciation spelling|obs-sp|abb|dim of|onlyin|syn of|syn-of|altcase|ao|io|clip|rareform|past participle|ellipse of|ellipsis|obssp|standspell|back-form|abbr of|alt sp|init of|obs sp|alt case|clip of|honor alt case|stand sp|alt form|alt form of|obs form)$/:
tpar[0]=trep_text[tpar[0]];

case /^(contraction of|dated form of|alternative capitalization of|informal spelling of|nonstandard spelling of|alternative spelling of|obsolete spelling of|alternative form of|alternate form of|abbreviation of|acronym of|rare spelling of|archaic spelling of|obsolete form of|eye dialect of|agent noun of|initialism of|synonym of|alternate spelling of|rare form of|eye dialect|only used in|medieval spelling of|superseded spelling of|euphemistic spelling of|alternative term for|feminine noun of|alternative form of|alternative case form of|short of|common misspelling of|only in|pejorative of|attributive of|short for|euphemistic form of|eye-dialect of|nonstandard form of|short form of|short for|diminutive of|superlative of|comparative of|augmentative of|reflexive of|apocopic form of|obsolete form of|short form of|informal form of|dated spelling of|pronunciation spelling of|former name of|superseded form of|clipping of|alternative typography of|supine of|nominalization of|construed with|syncopic form of|perfect participle of|obsolete typography of|present active participle of|alternative plural of|ellipsis of|aphetic form of|masculine singular past participle of|deliberate misspelling of|uncommon form of|early form of|present tense of|verbal noun of|standard form of|misconstruction of|alternative name of|second-person singular past of|archaic form of|elongated form of|eggcorn of|pronunciation respelling of|past of|attributive form of|spelling of|present of|comparative form of|superlative form of|participle of|endearing form of|singulative of|substantivisation of|frequentative of|perfective form of|imperfective form of|negative of|iterative of|alternative capitalisation of|misspelling form of|late form of|second-person singular of|definite of|blend of|past participle form of|alternative form of|diminutive plural of|causative of|definite singular of|female equivalent of|feminine equivalent of|feminine of|masculine of|neuter of|indefinite plural of|masculine noun of)$/:
outp = tpar[0] " ";

if(("lang" in tpar) && (tpar[1]!="")) {
if(tpar[1] ~ /\[\[/)
	outp = outp tpar[1];
else outp = outp "[[" tpar[1] "]]";
}
else {
if(tpar[2] ~ /\[\[/)
	outp = outp tpar[2];
else outp = outp "[[" tpar[2] "]]";
}

return outp;


# template-name [[{{1}}]] or template-name {{1}} (no lang parameter, language-specific template)
case /^(en-simple past of|en-third-person singular of|en-past of|en-comparative of|en-superlative of|en-irregular plural of|en-archaic second-person singular of|en-third person singular of|en-archaic third-person singular of|fr-post-1990|ru-abbrev of|ru-initialism of|ru-pre-reform|ru-acronym of|ru-alt-ё|cs-imperfective form of|hu-case|cretan dialect form of|en-archaic second-person singular past of|el-Italiot dialect form of|el-Cretan dialect form of|el-Maniot dialect form of|el-Cypriot dialect form of|la-praenominal abbreviation of|zh-original|zh-abbrev|zh-only|zh-used|zh-alt-form|zh-classifier|zh-short|zh-only used in|zh-used in|zh-erhua form of|zh-altterm|zh-also|pinread|pinof|zh-character component|zh-misspelling|cmn-erhua form of)$/:
tpar[0]=trep_text[tpar[0]];

case /^(European Portuguese form of|European Portuguese spelling of|(Italiot|Cretan|Maniot|Cypriot) dialect form of|British and International English spelling of|native or resident of|abbreviated|praenominal abbreviation of|pinyin reading of)$/:

outp = tpar[0] " ";
if(tpar[1] ~ /\[\[/)
	outp = outp tpar[1];
else outp = outp "[[" tpar[1] "]]";
return outp;


# templates replaced by first unnamed parameter
case /^(unsupported|w|W|non[-]gloss definition|n[-]g|ngd|taxlink|non gloss definition|non[-]gloss|non gloss|spelink|pedlink|def|IPAchar|def[-]date|smallcaps|sc|defdt|honoraltcaps|ja-r|glossary|glink|taxlinknew|upright|wtorw|pedia|keyword|swp|nobold|en-phrase|sub|overline|ja-def|ja-l|ko-inline|zh-m|IPAfont)$/:
return tpar[1];

# templates to be replaced by "{templatename}"
case /^(indeclinable|pf[.]|plural|monotonic|poly)$/:
tpar[0] = trep_text[tpar[0]];
case /^(impf|dual)$/:
return sob tpar[0] scb;

# templates to be replaced by templatename
case /^(abbreviation-old)$/:
tpar[0]=trep_text[tpar[0]];

case /^(CE|BC|given name|surname|historical given name|AD|praenomen|[.][.][.]|BCE|B[.]C[.]E[.]|USstate|A[.]D[.]|C[.]E[.]|translation only|B[.]C[.]|forename|sic)$/:
return  tpar[0];

# case-gov
case "case-gov":
return "(+ " tpar[2] ")";

# &oth, &lit
case /^[&]amp[;](lit|oth)$/:
outp = "See:";
for(i=1;i in tpar;i++) {
	if(tpar[i] ~ /\[\[/) 	outp = outp tpar[i];
	else outp = outp " [[" tpar[i] "]]";
}
return outp;

# templates replaced by 2nd unnamed parameter, e.g. lang-template
case /^(lang|cog|quote|w2)$/:
return tpar[2];

case "syndiff":
return "see synonyms at " tpar[2];

# place-template
# TODO: proper link?
case /^place($|[:].+$)/:
if((2 in tpar) && (tpar[2] != "")) outp = "[[" title "]] (" tpar[2] ")";
	else outp = "[[" title "]] (placename)";
# print outp;
return outp;

# etyl template
case "etyl":
return iso2lang(tpar[1]);

# bor/der
case /^(bor|der)$/:
outp = iso2lang(tpar[2])
if((3 in tpar) && (tpar[3] != "-")) outp = outp " " tpar[3];
return outp;

case "used in phrasal verbs":
outp = "used in a phrasal verb: [[" tpar[1] "]]"; 
if("t" in tpar) outp = outp " (" tpar["t"] ")";
return outp;

case /^(noncog|ncog|noncognate)$/:
return iso2lang(tpar[1]) " " tpar[2];

case /^(ux|uxi|usex)$/:
outp = tpar[2];
if(3 in tpar) outp = outp " ― " tpar[3];
if("t" in tpar) outp = outp " ― " tpar["t"];
return outp;

case "nbsp":
return " ";

case "circa2":
return "ca. " tpar[1];

case /^(c[.]|C[.])$/:
return tpar[1] "th c.";


# TODO: from fields
case "standard spelling of":
if("lang" in tpar) return "alternative spelling of " tpar[1];
else return "alternative spelling of " tpar[2];

# frac template
case "frac":
if(3 in tpar) return tpar[1] " " tpar[2] "/" tpar[3];
if(2 in tpar) return tpar[1] "/" tpar[2];
return "1/" tpar[1];

case /^(SI-unit|SI-unit-abb2|SI-unit-2|SI-unit-abb|SI-unit-np)$/:
return "an SI unit";

case "nuclide":
return " _" tapar[2] "^" tpar[1] tpar[3];

case/^(affix|compound|suffix|confix)$/:
if(2 in tpar) outp = outp "[[" tpar[2] "]]";
if(3 in tpar) outp = outp " + [[" tpar[3] "]]";
return outp;

case "CURRENTYEAR":
return "2019";

#############################
# language specific templates
#############################
# German
case "de-superseded spelling of":
return "obsolete spelling of " tpar[1];

case "de-plural noun":
if(headline == 1) {
if(1 in tpar) gend = gend sob tpar[1] "p" scb;
	else gend = gend sob "p" scb;
}
return "";

# Portuguese:
case /^(pt-obsolete.*|pt-superseded.*)$/:
return "obsolete spelling of " tpar[1]; 

case "pt-pron def":
if(tpar[2] ~ /[1-3]/)
	outp = tpar[2] ". person" tpar[3] ". "  tpar[1] "pronoun";
else outp = tpar[3] ". " tpar[4] ". form of "  tpar[1] " " tpar[2];
return outp;

case /^pt-pronoun-with-[nl]/:
outp = "alternative form of [[";
if(tpar[1] == "m") outp = outp "o";
	else   outp = outp "a";
if(tpar[1] == "pl")  outp = outp "s";
outp = outp "]]";
return outp;

case "+preo":
outp = " [+ " tpar[2] " (object)";
if(3 in tpar) outp = outp " = " tpar[3];
if("means" in tpar) outp = outp " = " tpar["means"];
outp = outp "]";
return outp;

case "+obj":
outp = " [+ " tpar[2];
if(3 in tpar) outp = outp " " tpar[3];
if(4 in tpar) outp = outp " " tpar[4];
if("means" in tpar) outp = outp " = " tpar["means"];
outp = outp "]";
return outp;

# Spanish and others
# get gender from "es-noun", "es-proper noun" and other languages
case /^((es|it|pt|fr|de|nl|pl|mk|el)-noun|pt-noun-form|(es|fr|pt|it|de|nl|pl|mk)-proper noun|el-noun-proper|it-noun-pl|it-plural noun)$/:
if(headline == 1) {
	if((1 in tpar)&&(tpar[1] != "")) gend = gend sob tpar[1] scb;
	if(("g" in tpar)&&(tpar["g"] != "")) gend = gend sob tpar["g"] scb;
	if(("g1" in tpar)&&(tpar["g"] != "")) gend = gend sob tpar["g1"] scb;
	if(("g2" in tpar)&&(tpar["g2"] != "")) gend = gend sob tpar["g2"] scb;
	if(("g3" in tpar)&&(tpar["g3"] != "")) gend = gend sob tpar["g3"] scb;
	if((tpar[0] == "it-noun-pl")||(tpar[0] == "it-plural noun")) gend = gend sob "p" scb;
}
return "";

# Serbo-Croatian, Danish
case /^(sh-noun|sh-proper noun|da-noun|da-noun-pl)$/:
if(headline == 1) {
	if(("g" in tpar)&&(tpar["g"] != "")) gend = gend sob tpar["g"] scb;
}
return "";

case /^(sh-verb)$/:
if(headline == 1) {
	if(("a" in tpar)&&(tpar["a"] != "")) {
		gend = gend " " tpar["a"];
		if((gend==" dual")||(gend==" ip")||(gend==" impf-pf")||(gend==" pf-impf")) gend = " impf pf";
}
}
return "";

# Finnish
case "fi-infinitive of":
return "infinitive of " tpar[1]; 

# Latin
case "NL.":
return "New Latin";

# get gender from the head-template la-noun:
case "la-noun":
if(headline == 1) {
#for(i in tpar) print i, tpar[i];
if(3 in tpar) gend = gend sob tpar[3] scb;
if("g2" in tpar) gend = gend sob tpar["g2"] scb;
if("g3" in tpar) gend = gend sob tpar["g3"] scb;
}
else print "#WARNING: head-template on defline, page: \"" title "\", line: \"" $0 "\"" >fixme;
return "";

# get gender from la-proper noun
case "la-proper noun":
if(headline == 1)
	if(3 in tpar) gend = gend sob tpar[3] scb;
return "";

# Polish and Czech verb
# get perfective, imperfective from pl-verb:
case /^(pl-verb|cs-verb)$/:
if(headline ==1) { 
	if("a" in tpar) {
		gend = " " tpar["a"];
		if(gend==" i") gend = " impf";
        	if(gend==" p") gend = " pf";
}
}
else print "#WARNING: misplaced template pl-verb, page: \"" title "\", line: \"" $0 "\"" >fixme;
return "";

# Macedonian verb
case /^(mk-verb)$/:
if(headline ==1) { 
	if(1 in tpar) {
		gend = " " tpar["1"];
}
}
else print "#WARNING: misplaced template mk-verb, page: \"" title "\", line: \"" $0 "\"" >fixme;
return "";

# Russian
# get perfective, imperfective from ru-verb and verb-alt-ё:
case /^(ru-verb|verb-alt-ё)$/:
if(headline ==1) 
	{if(2 in tpar) gend = " " tpar[2];}
else print "#WARNING: misplaced template ru-noun, page: \"" title "\", line: \"" $0 "\"" >fixme;
return "";

# Russian and Czech gender
case /^(ru-noun|ru-noun-alt-ё|ru-proper noun|ru-proper noun-alt-ё)$/:
if(headline == 1) 
	if((2 in tpar)&&(tpar[2] != "")) gend = gend sob tpar[2] scb;
case /^(ru-noun[+]|ru-proper noun[+]|cs-noun|cs-proper noun)$/:
if(headline == 1) {
	if(("g" in tpar)&&(tpar["g"] != "")) gend = gend sob tpar["g"] scb;
	if(("g1" in tpar)&&(tpar["g"] != "")) gend = gend sob tpar["g1"] scb;
	if(("g2" in tpar)&&(tpar["g2"] != "")) gend = gend sob tpar["g2"] scb;
	if(("g3" in tpar)&&(tpar["g3"] != "")) gend = gend sob tpar["g3"] scb;
}
return "";

# pronunciation templates
case /^(IPA)$/:
if(headline == 1) {
	if(("lang" in tpar) && (tpar[1]!="")) ipa=tpar[1];
	else {if(tpar[2]!="") ipa=tpar[2];}
	gsub(/(\/|\[|\])/, "", ipa);
	}
return "";

case /^(it-stress|it-IPA)$/:
if(headline == 1) {
	if(1 in tpar) outp = tpar[1]
	else outp = title
if(enable_lua == 1) {
	luascript = "cd Lua_Modules/ && ./it-IPA.lua";
	print outp |& luascript; close(luascript, "to");
	luascript |& getline outp; close(luascript);
#	print outp
	if((outp != "nil")&&(outp != "")) ipa=outp;
}
else	ipa = outp; 

gsub(/\//, "", ipa);
}
return "";

case /^(zh-pron)$/:
# print "in zh-pron"
if(headline == 1) {
	if(iso == "cmn") {
		if(("m" in tpar)&&(tpar["m"] != "")) ipa = tpar["m"]
		else ipa = "---"
	}
}
return "";

# Czech
case "cs-reflexive":
outp = reflexive
if(tpar[1]=="i") outp = outp ", used with si";
else outp ", used with se";

if(template_number == 1) {
	LHS_qualifier = LHS_qualifier outp; 
	return ""; 
}

outp = "[" outp "]";
return outp;

# Dutch
case "nl-pronadv of":
return "pronominal adverb form of " tpar[1] " + " tpar[2];

case "uncertain":
return  sob "uncertain meaning" scb;

# names of Latin letters
case "Latn-def":
outp = outp "letter";
if(4 in tpar) outp = outp ": [[" tpar[4] "]]";
if(5 in tpar) outp = outp ", [[" tpar[5] "]]";
if(6 in tpar) outp = outp ", [[" tpar[6] "]]";
if(7 in tpar) outp = outp ", [[" tpar[7] "]]";
return outp;

# Greek
case "el-demonym":
outp = ""
if(1 in tpar) outp = outp "[[" tpar[1] "]]"
return outp " (a person from " tpar["place"] ")";

# Chinese
case "zh-l":
if(1 in tpar) outp = tpar[1];
if("tr" in tpar) outp = outp " /" tpar["tr"] "/";
return outp;

case "zh-see":
if(1 in tpar) {
	if(headline == 1) first = tpar[1];
	else { return "see " tpar[1];}
}

case "zh-mw":
outp = "(Classifier: "
for(i=1;i in tpar;i++) {outp = outp tpar[i];}
outp = outp ")";
return outp;

case "zh-short-comp":
outp = "short fo "
for(i=1;i in tpar;i++) {outp = outp tpar[i];}
if("t"in tpar) outp = outp " (" tpar["t"] ")";;
return outp;

case "zh-sum of parts":
outp = "sum of parts of"
for(i=1;i in tpar;i++) {outp = outp " " tpar[i];}
return outp;

case "zh-div":
return "(～ " tpar[1] ")";

case /^(†|zh-obsolete|zh-no-solo|zh-o)$/:
return "[obsolete]";

case /^(zh-hd|‡|zh-hg|zh-hist-ghost|zh-historical-ghost)$/:
return "[historical dictionaries]";

case "zh-alt-lb":
return "[alternative form " tpar[1] "]";

case "zh-used2":
if(tpar[1] == "n") return "used in personal names";
if(tpar[1] == "p") return "used in place names";
if(tpar[1] == "c") return "used in compounds";
if(tpar[1] == "t") return "used in transcriptions of foreign words";
return "";

case /^(zh-synonym|zh-synonym of)$/:
outp = "synonym of " tpar[1];
if(2 in tpar) outpu = outp " (" tpar[2] ")";
return outp

case /^(zh-alt-name|zh-altname|zh-alt-term)$/:
outp = "alternative name for " tpar[1];
if(2 in tpar) outpu = outp " (" tpar[2] ")";
return outp

case /^(zh-old-name)$/:
outp = "old name for " tpar[1];
if(2 in tpar) outpu = outp " (" tpar[2] ")";
return outp

case /^(zh-subst-char)$/:
outp = "substitute character for " tpar[1];
if(2 in tpar) outpu = outp " (" tpar[2] ")";
return outp

# soplink
case "soplink":
for(i=1;i in tpar;i++) {
if (tpar[i] !~ /[-\ \/]/) outp = outp  "[[" tpar[i] "]]";
	else outp = outp  tpar[i];
}
return outp;

case "PAGENAME":
return title;

case "sup":
return "<sup>" tpar[1] "</sup>";

####################
# inflected forms:
####################
# output template-name {{1}}
case /^(present participle of|past participle of|feminine plural past participle of|feminine singular past participle of|masculine plural past participle of|feminine past participle of|masculine plural of|feminine plural of|plural of|singular of|uncommon spelling of|imperative of|gerund of|plural form of|neuter singular of|feminine singular of|misspelling of|past tense of|(vocative|nominative|genitive|dative|accusative) (singular of|plural of|of)|combining form of)$/:

outp = tpar[0] " ";
if(("lang" in tpar) && (tpar[1]!="")) {
if(tpar[1] ~ /\[\[/)
	outp = outp tpar[1];
else outp = outp "[[" tpar[1] "]]";
}
else {
if(tpar[2] ~ /\[\[/)
	outp = outp tpar[2];
else outp = outp "[[" tpar[2] "]]";
}

return outp;

# TODO: gloss, alt-text and tr and type of form
# accepts alternatively lang or 1st unnamed parameter
case /^(form of)$/:
if(("lang" in tpar) && (tpar[1]!="")) {
	outp = tpar[1] " form of " tpar[2];
	}
else {
	outp = tpar[2] " form of " tpar[3];
	}
return outp;

# TODO: alt-text 
case /^(conjugation of|inflection of|infl of|noun form of|verb form of)$/:
if(("lang" in tpar) && (tpar[1]!="")) {
for(i=3;i in tpar;i++) {
outp =  outp sc2txt(tpar[i]) " ";}
if(tpar[1] ~ /\[\[/) outp = outp "form of " tpar[1];
	else outp = outp "form of [[" tpar[1] "]]";
		}
else {
for(i=4;i in tpar;i++) {
outp =  outp sc2txt(tpar[i]) " ";}
if(tpar[2] ~ /\[\[/) outp = outp "form of " tpar[2];
	else outp = outp "form of [[" tpar[2] "]]";
	}
return outp;

case "it-adj form of":
for(i=2;i<=4;i++) 
	if(i in tpar) outp = outp sc2txt(tpar[i]) " ";
outp = outp " form of " tpar[1]; 
return outp;

case "es-verb form of":
if("region" in tpar) LHS_qualifier = LHS_qualifier tpar["region"];
if("formal" in tpar) {
	tpar["formal"] = sc2txt(tpar["formal"]);
	if(tpar["formal"] == "yes") outp = outp "formal ";
	if(tpar["formal"] == "no") outp = outp "informal ";
}
if("pers" in tpar) tpar["person"] = tpar["pers"];
if("person" in tpar) outp = outp  sc2txt(tpar["person"]) " ";
if("num" in tpar) tpar["number"] = tpar["num"];
if("number" in tpar) outp = outp  sc2txt(tpar["number"]) " ";
if("voseo" in tpar) outp = outp "voseo ";
if("sense" in tpar) outp = outp sc2txt(tpar["sense"]) " ";;
if("tense" in tpar)
	if( sc2txt(tpar["tense"]) == "conditional") tpar["mood"] = "conditional";
if("mood" in tpar) {
	tpar["mood"] = sc2txt(tpar["mood"]);
	if(tpar["mood"] !~ /(conditional|imperative|past-participle|gerund)/)
		outp = outp sc2txt(tpar["tense"]) " ";
	outp = outp tpar["mood"] " ";
}
if("verb" in tpar) tpar[1] = tpar["verb"];
if("inf" in tpar) tpar[1] = tpar["inf"];
if("infinitive" in tpar) tpar[1] = tpar["infinitive"];
outp = outp "form of " tpar[1];
return outp;

case "es-compound of":
outp = outp "coumpound of the verb ";
if(tpar["mood"]~/inf/) outp = outp tpar[1] tpar[2];
	else outp = outp  "form " tpar[3];
outp = outp " and the pronoun";
if(5 in tpar) outp = outp "s";
if(4 in tpar) outp = outp  " " tpar[4];
if(5 in tpar) outp = outp  " and " tpar[5];
return outp;

case "es-adj form of":
if(2 in tpar) outp = outp  sc2txt(tpar[2]) " ";
if(3 in tpar) outp = outp  sc2txt(tpar[3]) " ";
if(4 in tpar) outp = outp  sc2txt(tpar[4]) " ";
if(outp != "") outp = outp "form ";
if(1 in tpar) outp = outp  "of " tpar[1];
return outp;

case "pt-verb form of":
if((6 in tpar)&&(tpar[6] != ""))  outp = outp sc2txt(tpar[6]) " ";
if((5 in tpar)&&(tpar[5] != ""))  outp = outp tpar[5] " ";
if((4 in tpar)&&(tpar[4] != ""))  outp = outp tpar[4] " ";
if(3 in tpar)  outp = outp tpar[3] " ";
if(1 in tpar)  outp = outp "of " tpar[1] " ";
if("dialect" in tpar) LHS_qualifier = LHS_qualifier tpar["dialect"];
return outp;

case /^(pt-noun form of|pt-adj form of|pt-article form of)$/:
if(2 in tpar)  outp = outp sc2txt(tpar[2]) " ";
if(3 in tpar)  outp = outp sc2txt(tpar[3]) " ";
if(4 in tpar)  outp = outp sc2txt(tpar[4]) " ";
if(1 in tpar) {
	outp = outp  "form of "; 
	if(tpar[0] ~ /pt-article form of/) outp = outp "the article ";
	outp = outp tpar[1];
}
return outp;

case /^(pt-ordinal form|pt-ordinal def)$/:
if(tpar[1] ~ /[1-9]/) outp = outp sc2txt(tpar[2]) " of " tpar[1] "º";
	else outp = outp sc2txt(tpar[2]) " form of " tpar[1] "o";
return outp;

case "pt-adv form of":
return sc2txt(tpar[2]) " form of " tpar[1];

case "de-verb form of":
if(2 in tpar)  outp = outp sc2txt(tpar[2]) " ";
if(3 in tpar)  outp = outp sc2txt(tpar[3]) " ";
if(4 in tpar)  outp = outp sc2txt(tpar[4]) " ";
if(5 in tpar)  outp = outp "subordinate clause form ";
if(1 in tpar)  outp = outp  "of " tpar[1]; 
return outp;

# TODO: manual and automatic forms
case "pt-verb-form-of":
# TODO: compound parameters:
case "de-form-noun":
case /^(de-inflected form of|pt-cardinal form of|pt-apocopic-verb|inflected form of|de-du contraction|de-umlautless spelling of|de-zu-infinitive of)$/:
return trep_text[tpar[0]] " " tpar[1];

# TODO: shortcuts conflict with other templates
case "de-form-adj":
return trep_text[tpar[0]] " " tpar[4];

# unknown templates are deleted
default:
if(headline != 1)
	print "#WARNING: deleted unknown template: {{" tpar[0] "}} on page: \"" title "\" on line: \"" $0 "\"" >fixme;
return "";
}
}

#####################################
function get_multiline_template(line,       bracecount)
{
bracecount = gsub("{", "{", line) - gsub("}", "}", line);

for(;;) {
# print "bracecount: " bracecount;
if(bracecount < 0) print "# Warning: Too many closing braces in entry: \"" title "\", on line: " line >fixme;
if(bracecount == 1) {
	print "# Warning: stray open brace in entry: \"" title "\",on line: " line >fixme;
	break;
}

if(bracecount <= 0) break;

if(index("</text>", line) != 0) {
	print "# Error: Closing braces not found at end of entry: in entry: \"" title "\", ignoring line: " line >fixme;
	next;
}

if($0 ~ /^([=][=]|[-][-][-][-])/) {
	print "# Error: Closing braces not found at end of section at entry: \"" title "\", ignoring line: " line >fixme;
	next;
}
 
if (getline <= 0) {
	print "# Error: Closing braces not found at end of file." >fixme;
	next;
}

bracecount = bracecount + gsub("{", "{") - gsub("}", "}");
line =  line $0;

# remove commented linebreaks
sub(/&lt;[!][-][-].*[-][-]&gt;/, "", line);

}

return line;
}

#####################################
function parse_templates(input,         i, j, k, ta, sa, nt, ts, na, targs, n2, a2, tpar, rep, outp)
{
# parses string for templates 
# and calls replace_templat() for each template found
# then returns a replacement string
# THIS FUNCTION HAS TO BE CALLED MULTIPLE TIMES FOR STRINGS WITH NESTED TEMPLATES

# replace bars inside wiki-links and {{!}} with wlbar
wlbar="_WLB_";
# replace single braces
sob="_SOB_";
scb="_SCB_";

gsub(/\{\{[!]\}\}/, wlbar, input);
gsub(/\{\{[=]}\}/, "\\&equals;", input);


input = gensub(/([^\{])(\{)([^\{])/, "\\1" sob "\\3", "g", input);
input = gensub(/([^\}])(\})([^\}])/, "\\1" scb "\\3", "g", input);

# is this necessary?
delete ta; delete sa;

# split input string into templates (ta[1, ..., n]) and non-template strings (sa[0, ..., n])
nt = patsplit(input, ta, /\{\{[^}{]*\}\}/, sa);

output = "";
for(i=1; i<=nt; i=i+1) {
	ts = ta[i]
#	replace bars inside wiki-links with wbar
	ts = gensub(/(\[\[[^\]]*)(\|)([^\]]*\]\])/, "\\1" wlbar "\\3", "g", ts); 
#	remove spaces	
	gsub(/[\ ]*[=][\ ]*/, "=", ts);
	gsub(/[\ ]*\|[\ ]*/, "|", ts);
	gsub(/[\ ]*[}][}]/, "}}", ts);


#	split template arguments into array targs	
	sub(/\{\{/, "", ts); sub(/\}\}/, "", ts);
	na = split(ts, targs, "|");

	k = 0; delete tpar;
	for(j=1; j<=na; j=j+1) {
		n2 = split(targs[j], a2, "=");
		# prevent uninitialized  a2[1] for empty template argument targs[j]
		if(n2==0)  a2[1] = "";
		if(n2 <= 1) {tpar[k] = a2[1]; k=k+1;}
		else        tpar[a2[1]] = a2[2];
}
#	debug output
#	for (test in tpar) print test, "\"" tpar[test] "\"";
#	now call replace_template function which returns a replacement string for the template
	template_number = i;
	rep = replace_template(tpar, k-1);
#	print rep;	
	ta[i] = rep;
}
outp = "";
if(0 in sa) outp = sa[0]; 
for(i=1; i<=nt; i=i+1) {outp = outp ta[i]; if(i in sa) outp = outp sa[i];}
return outp;
}

#####################################
function printout(out) {
# does formatting before output
# then prints to stdout

# remove XML code at the end of last line
gsub(/<\/text>/,"",out);

# fix tripple brackets which might cause trouble later
# asume inner wikilink
gsub(/\[\[\[/,"[ [[",out);
gsub(/\]\]\]/,"]] ]",out);

# remove dots at end of line	
gsub(/\.[\ ]*$/,"",out);

# convert back escaped special characters (template-parsing)
gsub(wlbar, "|", out); gsub(sob, "{", out); gsub(scb, "}", out);

# convert special XML formatting like &lt; to HTML
gsub(/&amp;/,"\\&",out);
gsub(/&lt;/,"<",out);
gsub(/&gt;/,">",out);
gsub(/&amp;/,"\\&",out);
gsub(/&quot;/,"\"",out);
gsub(/&nbsp;/, " ", out);
gsub(/&hellip;/, "...", out);
gsub(/&quot;/, "\"", out);
gsub(/&[mn]dash;/, "-", out);
gsub(/&thinsp;/, "", out);
gsub(/&minus;/, "-", out);
gsub(/&equals;/, "=", out);
gsub(/&equiv;/, "≡", out);
gsub(/&rarr;/, "→", out);
gsub(/&harr;/, "↔", out);
gsub(/&#39;/, "'", out);
gsub(/&#61;/, "=", out);
gsub(/&frac12;/, "½", out);
gsub(/&ldquo;/, "\"", out);
gsub(/&rdquo;/, "\"", out);
gsub(/&prime;/, "′", out);

# NOTE: these must be done after converting '&lt;' -> '<'  and '&gt;' -> '>'
# remove <ref ... \>
gsub(/<ref[^>]*\/>/,"",out);
# remove <ref [name=....]> blabla </ref> OK?
gsub(/<ref[^>]*>.*<\/ref>/,"",out);
# these are misformated refs:
# remove <ref [name=....]>
gsub(/<ref[^>]*>/,"",out);
gsub("<ref>", "", out);

# remove one-line <!-- commented text -->
gsub(/<!--[^>]*-->/,"",out); 

# remove extra spaces
gsub(/[\ ]+/, " ", out);

# remove remaining "<!--" (will prevent display of wiki-file)
gsub(/<!--/,"", out);
gsub(/[<]br[\ ]*[/][>]/, "", out);

# these are from formatting errors:
gsub(/\[\]/, "", out);
gsub("{}", "", out);

if(remove_wikilinks==1) {
#	wiki-links and italicizing, bolding
	out = gensub(/([[][[])([^]|]*\|)([^]]*)([]][]])/ , "\\3", "g", out);
	out = gensub(/([[][[])([^]]*)([]][]])/ , "\\2", "g", out);
	gsub(/['][']+/, "", out);

#	<sub> and <sup>
	gsub(/<sup>/, "^", out);  gsub(/<\/sup>/, "", out);
	gsub(/<sub>/, "", out);  gsub(/<\/sub>/, "", out);
			 
#	<nowiki> 			
	gsub(/<nowiki>/, "", out); gsub(/<\/nowiki>/, "", out);	
}

# remove diacritics
out = remove_diacritics(lang, out);
#if(iso == "ru") 
#	out = gensub(/([аеёиоуыэюяАЕЁИОУЫЭЮЯ])(\xCC\x81|\xCC\x80)/, "\\1",  "g", out);

print out;
}

#####################################################
function remove_diacritics(generic_lang, text) {
# info about diacritics/vocalization removal is located in Module:languages/data2, data3
# languages/data gives the unicode codepoints which have to be converted to utf8-hex

switch (generic_lang) {

case "Russian":
text = gensub(/([аеёиоуыэюяАЕЁИОУЫЭЮЯ])(\xCC\x81|\xCC\x80)/, "\\1",  "g", text);
return text;

case "Bulgarian":
gsub(/(\xCC\x81|\xCC\x80)/, "", text);
gsub(/Ѐ/, "Е", text);
gsub(/ѐ/, "е", text);
gsub(/Ѝ/, "И", text);
gsub(/ѝ/, "и", text);
return text;

case "Macedonian":
gsub(/\xCC\x81/, "", text);
return text;

case "Serbo-Croatian":
gsub(/(\xCC\x81|\xCC\x80|\xCC\x8F|\xCC\x91|\xCC\x84|\xCC\x83)/, "", text);
gsub(/ȀÀȂÁĀÃ/, "A", text);
gsub(/ȁàȃáāã/, "a", text);
gsub(/ȄÈȆÉĒẼ/, "E", text);
gsub(/ȅèȇéēẽ/, "e", text);
gsub(/ȈÌȊÍĪĨ/, "I", text);
gsub(/ȉìȋíīĩ/, "i", text);
gsub(/ȌÒȎÓŌÕ/, "O", text);
gsub(/ȍòȏóōõ/, "o", text);
gsub(/ȐȒŔ/, "R", text);
gsub(/ȑȓŕ/, "r", text);
gsub(/ȔÙȖÚŪŨ/, "U", text);
gsub(/ȕùȗúūũ/, "u", text);
gsub(/Ѐ/, "Е", text);
gsub(/ѐ/, "е", text);
gsub(/ӢЍ/, "И", text);
gsub(/Ӯ/, "У", text);
gsub(/ӯ/, "у", text);
return text;

case "Arabic":
gsub(/\xD9\xB1/, "\xD8\xA7", text);
gsub(/\xD9(\x8B|\x8C|\x8D|\x8E|\x8F|\x90|\x91|\x92|\xB0|\x80)/, "", text);
return text;

case "Persian":
gsub(/\xD9(\x8E|\x8F|\x90|\x91|\x92)/, "", text);
return text;

case "Hebrew":
gsub(/\xD6(\x91|\x92|\x93|\x94|\x95|\x96|\x97\x98|\x99|\x9A|\x9B\x9C|\x9D|\x9E|\x9F|\xA0|\xA1|\xA2|\xA3|\xA4|\xA5|\xA6|\xA7|\xA8|\xA9|\xAA|\xAB|\xAC|\xAD|\xAE|\xAF|\xB0|\xB1|\xB2|\xB3|\xB4|\xB5|\xB6|\xB7|\xB8|\xB9|\xBA|\xBB|\xBC|\xBD|\xBF)/, "", text)
gsub(/\xD7(\x80|\x81|\x82|\x83|\x84|\x85|\x86|\x87)/, "", text)
return text;

default:
return text;
}
}
#
#######################################
function linktotext(text) {
gsub(/_WLB_/, "|", text);
text = gensub(/([[][[])([^]|]*\|)([^]]*)([]][]])/ , "\\3", "g", text);
text = gensub(/([[][[])([^]]*)([]][]])/ , "\\2", "g", text);
return text;
}

######################################
# 	Main program
######################################

# get page title
/[<]title[>]/ { 
gsub(/^[^<]*[<]title[>]/, ""); gsub(/[<][/]title[>].*$/, ""); 
title=$0; 
#print title;
# reset everything except title:
langsect=0; pos= ""; gend = ""; gend2 = ""; pron=0; ipa1=""; ipa2=""; nestsec = 0;

# discard wrong namespaces
if(index(title,"Wiktionary:") != 0) title="";
if(index(title,"Template:") != 0) title="";
if(index(title,"Index:") != 0) title="";
if(index(title,"Appendix:") != 0) title="";
if(index(title,"User:") != 0) title="";
if(index(title,"Help:") != 0) title="";
if(index(title,"Citations:") != 0) title="";
}

{if(title=="") next;}

# discard non-useful lines (speedup and false "trans-see" lines from comment lines)
/<comment>|<\/?page>|<timestamp>|<id>|<\/?contributor>|<\/?revision>|<username>|<minor \/>/  {next;}
/^$/ {next;}

# desired LANG language section found
$0 ~ langhead {
langsect=1; 
# reset everything except title and langsect:
pos= ""; gend = ""; gend2 = ""; pron=0; ipa1=""; ipa2="";
#print lang, ": ", title; 
next;}

# any language section: reset everything except title
/^\x3D\x3D[^\x3D]+/ { 
langsect=0; pos= ""; gend= ""; gend2= ""; pron=0; ipa1=""; ipa2=""; 
next;
}

# language and title detection done; skip all lines if not inside LANG section
{if(langsect==0) next;}

# detect pronunciation section
/[=][=][=][ ]*Pronunciation/ {
pron=1; ipa1=""; ipa2="";
next;
}

# detect etymology and alternative forms section (might be nested inside POS)
# these might contain lists with # which otherwise get included
# skip if before POS (pos == "") 
/[=][=][=][ ]*(Etymology|Alternative forms)/ {
if(pos == "") pos = "-";
next;
}

# determine ipa1 and ipa2
$0 ~ defipa { 
#print "defipa detected"
if((pron==1)&&(ipa1=="")&&(enable_ipa==1)) {
#	print "processing defipa"
	gsub(/\{\{[!]\}\}/, wlbar, $0);
# print "parsing ipa1 info for: " title
	ipa = "";	
	headline=1;
# parse gender in headline-template via replace_template function
	HD = $0;
	HD = get_multiline_template(HD); 
	HD = parse_templates(HD);
# do we have nested headlines? would require parsing twice:
	parse_templates(HD);				
	ipa1=ipa;
	headline=0;
#	gsub(/\|lang\=[^|}]*/, "", $0);
#	ipa1=gensub(/(.*\{\{IPA\|[\/\[]*)([^}\|\/]*)([\/\]]*.*)/, "\\2", "g", $0); 
# print "def ipa " title :" " ipa1 >>"IPA.txt";
	next;
	}
}

$0 ~ altipa {
if((pron==1)&&(ipa2=="")&&(enable_ipa==1)) {
	gsub(/\{\{[!]\}\}/, wlbar, $0);
	ipa = "";	
	headline=1;
# parse gender in headline-template via replace_template function
	HD = $0;
	HD = parse_templates(HD);
# do we have nested headlines? would require parsing twice:
	parse_templates(HD);				
	ipa2=ipa;
	headline=0;	 
# print "alt ipa " title " " ipa2 >>"IPA.txt";
	next;
	}
}

# determine POS
# reset variables per POS
/\x3D\x3D\x3D/ { 
pos=""; gend=""; gend2=""; term_label="";
nestsec = 0;
}

/\x3D\x3D\x3D[\x20]*Noun[\x20]*[1-9]*\x3D\x3D\x3D/ { pos="n"; next;}
#/\x3D\x3D\x3D[\x20]*Verb[\x20]*\x3D\x3D\x3D/ { pos="v"; next;}
/\x3D\x3D\x3D[\x20]*Verb/ { pos="v"; next;}
/\x3D\x3D\x3D[\x20]*Adjective[\x20]*[1-9]*\x3D\x3D\x3D/ { pos="adj"; next;}
/\x3D\x3D\x3D[\x20]*Adverb([\x20]|\x3D)/ { pos="adv"; next;}
/\x3D\x3D\x3D[\x20]*Interjection[\x20]*[1-9]*\x3D\x3D\x3D/ { pos="interj"; next;}
/\x3D\x3D\x3D[\x20]*Article[\x20]*\x3D\x3D\x3D/ { pos="art"; next;}
/\x3D\x3D\x3D[\x20]*Proper[\x20]noun[\x20]*[1-9]*\x3D\x3D\x3D/ { pos="prop"; next;}
/\x3D\x3D\x3D[\x20]*Preposition[\x20]*\x3D\x3D\x3D/ { pos="prep"; next;}
/\x3D\x3D\x3D[\x20]*Postposition[\x20]*\x3D\x3D\x3D/ { pos="postp"; next;}
/\x3D\x3D\x3D[\x20]*\{\{initialism/ { pos="initialism"; next;}
/\x3D\x3D\x3D[\x20]*Numeral[\x20]*\x3D\x3D\x3D/ { pos="num"; next;}
/\x3D\x3D\x3D[\x20]*Cardinal num(ber|eral)[\x20]*\x3D\x3D\x3D/ { pos="cardinal num"; next;}
/\x3D\x3D\x3D[\x20]*Ordinal (number|numeral)[\x20]*\x3D\x3D\x3D/ { pos="ordinal num"; next;}
/\x3D\x3D\x3D[\x20]*Number[\x20]*\x3D\x3D\x3D/ { pos="num"; next;}
/\x3D\x3D\x3D[\x20]*\{\{acronym/ { pos="acronym"; next;}
/\x3D\x3D\x3D[\x20]*Acronym/ { pos="acronym"; next;}
/\x3D\x3D\x3D[\x20]*\{\{abbreviation/ { pos="abbr"; next;}
/\x3D\x3D\x3D[\x20]*Determiner[\x20]*\x3D\x3D\x3D/ { pos="determiner"; next;}
/\x3D\x3D\x3D[\x20]*Phrase[\x20]*\x3D\x3D\x3D/ { pos="phrase"; next;}
/\x3D\x3D\x3D[\x20]*Suffix[\x20]*[1-9]*\x3D\x3D\x3D/ { pos="suffix"; next;}
/\x3D\x3D\x3D[\x20]*Pronoun[\x20]*[1-9]*\x3D\x3D\x3D/ { pos="pron"; next;}
/\x3D\x3D\x3D[\x20]*Conjunction[\x20]*\x3D\x3D\x3D/ { pos="conj"; next;}
/\x3D\x3D\x3D[\x20]*Proverb[\x20]*\x3D\x3D\x3D/ { pos="proverb"; next;}
/\x3D\x3D\x3D[\x20]*Contraction[\x20]*\x3D\x3D\x3D/ { pos="contraction"; next;}
/\x3D\x3D\x3D[\x20]*(Particle|Enclitic Particle)[\x20]*\x3D\x3D\x3D/ { pos="particle"; next;}
/\x3D\x3D\x3D[\x20]*Symbol[\x20]*\x3D\x3D\x3D/ { pos="symbol"; next;}
/\x3D\x3D\x3D[\x20]*Prefix[\x20]*\x3D\x3D\x3D/ { pos="prefix"; next;}
/\x3D\x3D\x3D[\x20]*Letter[\x20]*\x3D\x3D\x3D/ { pos="letter"; next;}
/\x3D\x3D\x3D[\x20]*Abbreviation[\x20]*\x3D\x3D\x3D/ { pos="abbr"; next;}
/\x3D\x3D\x3D[\x20]*Initialism[\x20]*\x3D\x3D\x3D/ { pos="initialism"; next;}
/\x3D\x3D\x3D[\x20]*Idiom[\x20]*\x3D\x3D\x3D/ { pos="idiom"; next;}
/\x3D\x3D\x3D[\x20]*Affix[\x20]*\x3D\x3D\x3D/ { pos="affix"; next;}
/\x3D\x3D\x3D[\x20]*Adverbial phrase[\x20]*\x3D\x3D\x3D/ { pos="adv"; next;}
/\x3D\x3D\x3D[\x20]*Prepositional phrase[\x20]*\x3D\x3D\x3D/ { pos="prep"; next;}
/\x3D\x3D\x3D[\x20]*Participle[\x20]*\x3D\x3D\x3D/ { pos="v"; next;}
/\x3D\x3D\x3D[\x20]*Ambiposition[\x20]*\x3D\x3D\x3D/ { pos="ambip"; next;}
/\x3D\x3D\x3D[\x20]*Gerund[\x20]*\x3D\x3D\x3D/ { pos="v"; next;}
/\x3D\x3D\x3D[\x20]*Circumposition[\x20]*\x3D/ { pos="circump"; next;}
/\x3D\x3D\x3D[\x20]*Circumfix[\x20]*\x3D/ { pos="circumfix"; next;}
/\x3D\x3D\x3D[\x20]*(Interfix|Infix)[\x20]*\x3D/ { pos="interfix"; next;}
/\x3D\x3D\x3D[\x20]*Diacritical mark[\x20]*\x3D/ { pos="diacrit"; next;}
/\x3D\x3D\x3D[\x20]*Punctuation mark[\x20]*\x3D/ { pos="punct"; next;}
/\x3D\x3D\x3D[\x20]*Punctuation[\x20]*\x3D/ { pos="punct"; next;}
/\x3D\x3D\x3D[\x20]*Clitic[\x20]*\x3D/ { pos="clitic"; next;}
/\x3D\x3D\x3D[\x20]*Word[\x20]*\x3D/ { pos="unk"; next;}
/\x3D\x3D\x3D[\x20]*(Predicative|Predicate)[\x20]*\x3D/ { pos="pred"; next;}
/\x3D\x3D\x3D[\x20]*Combining form[\x20]*\x3D/ { pos="affix"; next;}
/\x3D\x3D\x3D[\x20]*Han character[\x20]*\x3D/ { pos="han"; next;}
/\x3D\x3D\x3D[\x20]*Classifier[\x20]*\x3D/ { pos="classifier"; next;}
/\x3D\x3D\x3D[\x20]*Logogram[\x20]*\x3D/ { pos="logogram"; next;}
#Chinese POS headlines
/\x3D\x3D\x3D[\x20]*Definition[s]*[\x20]*\x3D/ { pos="def"; next;}
/\x3D\x3D\x3D[\x20]*Romanization[s]*[\x20]*\x3D/ { pos="rom"; next;}
/\x3D\x3D\x3D[\x20]*Hanzi[\x20]*\x3D/ { pos="han"; next;}

#
## Usage notes etc. don't contain definitions and might contain lines starting with #, skip
/\x3D\x3D\x3D[\x20]*(Usage notes|Synonyms|Antonyms|Related (t|T)erms|Derived (t|T)erms|See also|Anagrams|References|Glyph origin)[\x20]*\x3D\x3D\x3D/ {
pos = "-";
next;
}

# These are supposed to be usage examples and synonyms; omit
/\x23\:|\x23\*/ {next;}

# discard entries without head-line
# use option "rm_headless_pos = 1" for languages with plain '''WORD''' 
# rather than {{head|iso|POS form|...}} headline of non-lemma entries
/^[']['][']/ {
if((rm_headless_pos == 1)&&(pos!="-")) {
if(index($0, "'''"title"'''") !=0) 
	{
# these POS have many inflected forms and the sections are filtered out
	if((pos=="adj")||(pos=="n")||(pos=="v")) { 
		pos="-";
# throw a warning so that these filtered entries can be fixed
		print "#WARNING: excluding entry on page: \"" title "\" without headline-template, line: " $0 >fixme;
}		
# all other POS are kept and a warning is thrown:
	else print "#WARNING: including entry on page: \"" title "\" without headline-template, line: " $0 >fixme;
}
}
next;
}

# form of headers, exclude current POS section
$0 ~ exclude_POS {pos="-"; next;}

# determine gender of nouns
$0 ~ nounhead  {
if((pos=="n")||(pos=="prop")) {	
# print "parsing gender info for noun: " title
	gend = "";	
	headline=1;
# parse gender in headline-template via replace_template function
	HD = $0;
	HD = parse_templates(HD);
# do we have nested headlines? would require parsing twice:
	parse_templates(HD);				
	headline=0;
}
# print "gend = " gend;
next;
}

$0 ~ verbhead {
# parse templates first, then look for verbatim labels
gend="";
headline = 1;
HD = $0;
HD = parse_templates(HD);
# do we have nested headlines? it would require parsing twice:
HD = parse_templates(HD);

# some headlines still have intransitive info as plain text 
if(match(HD, "intransitive") != 0) gend = (gend "i");
if(match(HD, "[^ni]transitive") != 0) gend = (gend "t");
if(match(HD, "ambitransitive") != 0) gend = (gend "it");
if(match(HD, "reflexive") != 0) gend = (gend "r");
if(match(HD, "pronominal") != 0) gend = (gend "p");
# remove all braces (fix for headlines havingq gender info)
gsub(sob, " ", gend);
gsub(scb, "", gend);
headline = 0;		
next;
}

# parse term-labels of misc headers:
/^[^#].*\{\{(term-label|tlb|term-context|tcx)/ {
headline = 1;
HD = $0;
HD = parse_templates(HD);
# do we have nested headlines? would require parsing twice:
HD = parse_templates(HD);
headline = 0;
}

# skip definition lines via exclude_defn filter
$0 ~ exclude_defn {next;}

# Chinese alternative forms, not on definition line
/\{\{zh-see\|/ {
if((langsect==1)&&(iso == "cmn")) {
headline=1;
first="";
HD = $0;
HD = parse_templates(HD);
headline = 0;
if(first != "") printout( "[[" title "]] {def} SEE: [[" first  "]] ::");
}}

# main section: format output lines
## exclude nested definitions
#/^[\x20]*\x23/ 	{ 
## include nested definitions
/^[\x20]*\x23+/ 	{ 

if((langsect==1)&&(pos != "-")&&(title!=""))
{
DL = $0;

############################################
# apply some fixed before parsing templates
############################################

# discard non-mandarin def. lines (pronunciation without mandarin)
if(ipa1 == "---") next;

# context -> label
gsub(/\{\{(cx|context)\|/, "{{lb|en|", DL);

# math formulas: fix errors cause by double braces in formulas
if(DL ~ /&lt;math&gt;/) {
DL = gensub(/(&lt;math&gt;[^&]*){{([^&]*&lt;\/math&gt;)/, "\\1\\{ {\\2", "g", DL);
DL = gensub(/(&lt;math&gt;[^&]*)}}([^&]*&lt;\/math&gt;)/, "\\1\\} }\\2", "g", DL);
}

# discard non-mandarin def. lines (pronunciation without mandarin)
if(ipa1 == "---") next;


###############################
# now parse the templates:
###############################
gend2="";
LHS_qualifier = "";

MAXNESTING = 3;
for(i=1; i<= MAXNESTING ; i = i+1) {
# find multiline templates 		
	DL = get_multiline_template(DL);	
	DL = parse_templates(DL);
# print DL;
	if(DL !~ /\{\{/) break;
}

if(DL ~ /\{\{|\}\}/) {
	print "#WARNING: on page: \"" title "\": skipping badly formatted input line: \"" $0 "\" or maybe to much template nesting, try to increase the \"MAXNESTING\" variable" >fixme;
	next;
}

# Latin reconstructed forms
if(lang=="Latin") sub(/Reconstruction[:]Latin\//, "*", LHS);

# remove "#" (\x23) and space
#gsub(/^[\x20]*\x23[\x20]*/,"",DL);			
gsub(/^[\x20]*\x23+[\x20]*/,"",DL);

# remove XML code at the end of last line
gsub(/<\/text>/,"",DL);

# remove leading punctuation
gsub(/^[\ \.,;\:]+/,"",DL);

# discard empty definition lines:
if(DL ~ /^[\ .\{\}\(\)\[\];\:]*$/) next;

##########################################
# now formatting the left hand side (LHS):
##########################################
pos2="";
if(pos == "n") {
	if(gend == "") {
		if(has_neuter==1) pos2 = "{noun}";
		else pos2 ="{n}";
}
	else pos2 = gend;
}

if(pos=="prop") {
	pos2 = "{" pos "}";
	if(gend != "") pos2 = pos2 " " gend;
}

if(pos=="v") {
#	if(gend2 == "")
#		pos2 = "{" pos gend "}";
#	else pos2 = "{" pos gend2 "}"
	pos2 = "{" pos gend2 gend "}";
}

# other cases
if(pos2 == "") pos2 = "{" pos "}";

# clean up pos2 (gender-info formatting)
# TODO this should go into a function 
gsub(sob, "{", pos2); gsub(scb, "}", pos2);
sub(/\{m-f\}/, "{mf}", pos2); 
sub(/\{m\}\{f\}/, "{mf}", pos2);

# Polish and Russian gender
pos2 = gensub(/(m|f|n)-an/, "\\1 anim", "g", pos2);
pos2 = gensub(/(m|f|n)-in/, "\\1 inan", "g", pos2);
pos2 = gensub(/(m|f|n)-pr/, "\\1 pers", "g", pos2);

gsub(/\}\{/, "} {", pos2);
pos2 = gensub(/([mfnc])-([sp])/, "\\1\\2", "g", pos2); 
if(pos2 == "") pos2 ="?";

# now print LHS
LHS = sprintf("[[%s]] %s",title,pos2);
# format LHS_qualifier and term_label:
if(term_label != "") {
if(LHS_qualifier != "") 
	LHS_qualifier = term_label ", " LHS_qualifier;
else LHS_qualifier = term_label;
}
if(LHS_qualifier != "") LHS = LHS " ["  LHS_qualifier "]";

# add pronunciation
if(enable_ipa==1) {
	if(ipa1!="") { 
		LHS = LHS " /" ipa1 "/ ";
		if(iso != "cmn") ipa1="";
		ipa2="";
	}

	if(ipa2!="") { 
		LHS = LHS " /" ipa2 "/ ";
		ipa1=""; ipa2="";
	}
} 

# the output line:
outp = LHS " :: " DL;

# wiki-link cleanup:
###################
gsub(/\#English/,"",outp);
gsub(/\[\[\|/,"[[",outp);

# rm #blabla from link inside square brackets
# first [[#bla|word]] -> [[title|word]] then other cases
outp=gensub(/(\[\[[#][^\|\]]*)(\|[^\]]*\]\])/, "[["title"\\2", "g", outp);
outp=gensub(/(\[\[[^\|\]]*[^ ])([ ]*[#][^\|\]]*)(\|[^\]]*\]\])/, "\\1\\3", "g", outp);
				
printout(outp);
if (pos == "") print "#UNKNOWN POS on page: \"" title "\", line: " $0 >fixme;
			
} 
}

$0 ~ warnmissing { 
# explicit lemma Category on entry
if((pos=="-")&&(rm_headless_pos==1)) 
	print "#WARNING possible missing head template (explicit POS-category) on page [["title"]]" >fixme;
}
