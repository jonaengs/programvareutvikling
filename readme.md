## <img src="http://134.209.228.155/static/itsbooking.png" alt="drawing" height="100px"/>
itsBooking er et system for koordinering mellom studenter, 
studentassistenter og emneansvarlig.

Systemet lar en emneansvarlig fastsette et maks antall studentassistenter på sal for gitte tidspunkt gjennom uka.
Studenassistenter kan så velge tidspunkt de vil sitte på sal basert på intervallene (2 timer)
emneansvarlig har fastsatt. Studenter vil så kunne reservere veiledingstimer i kvartersintervaller der det finnes
ledige studenassistener. 

Studenter vil også kunne laste opp øvinger/innleveringer som studentassistentene
og emneansvarlig kan vurdere og gi tilbakemelding på.  

Emneansvarlig kan legge ut en kunngjøring til alle studentassistenter i et emne.
Hver studenassistent har også mulighet til å kommunisere med emneansvarlig ved
å kommentere kunngjøringen. Emneansvarlig kan svare på disse kommentarene, som vil
skape en toveiskommunikasjon.

Det skal være et superbruker-grensesnitt slik at administrator kan kontrollere 
adgangsrettigheter for brukere samt ha mulighet til å opprette nye brukere. 
Administrator skal ha full tilgang til å manipulere backend. 

Emneansvarlig er knyttet opp mot ett enkelt fag, mens studentassistenter og studenter
kan være koblet opp mot et vilkårlig antall fag. 




## Motivasjon
Produktet er utarbeidet i samsvar med vår kunde Norsk universitet for ikke-tekniske
samfunnsvitere. 

## "Build status"
![](https://gitlab.stud.idi.ntnu.no/programvareutvikling-v19/gruppe-60/badges/dev/coverage.svg)
![](https://gitlab.stud.idi.ntnu.no/programvareutvikling-v19/gruppe-60/badges/dev/build.svg)

## Kode
Da prosjektet bygger på Python og Django har vi valgt å følge deres tilnærming til 
kodestil og dokumentasjon, [pep-8](https://www.python.org/dev/peps/pep-0008/) 
er altså implementert i alle pythonfiler. 

Målet har vært å skrive kode som i så stor grad som mulig er selvdokumenterende.
Dersom kodens funksjon eller hensikt ikke er tydelig, skal det legges ved en kommentar.

## Teknologi og rammeverk
[Django](https://www.djangoproject.com/),
[UIKit](https://getuikit.com/).

testing: 
[coverage](https://coverage.readthedocs.io/en/v4.5.x/).

lokal testing / dummy data: 
[requests](http://docs.python-requests.org/en/master/),
[faker](https://github.com/joke2k/faker),
[GoodDoggo](http://gooddoggo.dog/) [1](https://github.com/jonaengs/doggo-site) og [2](https://github.com/ingriddraagen/DoggoFace)

annet: 
[pillow](https://pillow.readthedocs.io/en/stable/)
(for Django image handling)  

## Installasjon
**NB!** Installasjon krever at du allerede har python 3.6+ og git installert.

For å kjøre siden lokalt: 
I kommandolinje (og i en passende mappe), kjør disse kommandoene:
~~~~shell
git clone https://gitlab.stud.idi.ntnu.no/programvareutvikling-v19/gruppe-60
~~~~
~~~~shell
cd gruppe-60
~~~~
~~~~shell
pip install -r requirements.txt
~~~~
~~~~shell
python manage.py migrate
~~~~
~~~~shell
python manage.py runserver 0.0.0.0:80
~~~~

For å se nettsiden: åpne en nettleser og skriv 'localhost' i søkefeltet. 
For å avslutte kan du gå inn i terminalen og trykke 'ctrl + c' på tastaturet 

Ved oppstart vil nettsiden være helt tom. Du kan da enten gå inn på 
'localhost/populate/' i nettleseren for å la et ferdiglaget script 
(itsBooking/populate_db.py) lage 'dummy-data' eller 
i terminalen kjøre kommandoen 'python manage.py createsuperuser', fullføre prosessen,
og så gå inn på 'localhost/admin', logge inn med din nye bruker og så 
sette opp systemet på egenhånd. 

Merk at nettsiden krever tre brukergrupper med spesifikke navn for å fungere. 
Disse må du selv lage hvis du velger å ikke bruke scriptet som følger med.
De tre gruppene må hete 'students', 'assistants', og 'course_coordinators'.
Avvik fra dette vil medføre at produktet ikke vil fungere optimalt.

Ved bruk av populate-scriptet vil det opprettes en haug med brukere, fordelt over 
de tre brukergruppene, for deg. Samtlige brukere har passord '123'. Brukernavn 
kan sees via admin-menyen, som du kan nå med superbrukeren som opprettes.
Denne brukeren har brukernavn 'admin' og passordet er '123'.  

## Server

For å sette opp siden på en server anbefaler vi at du følger 
[denne veiledningen](https://www.digitalocean.com/community/tutorials/how-to-set-up-django-with-postgres-nginx-and-gunicorn-on-ubuntu-18-04), 
men at du kloner repoet vårt istedenfor å lage et nytt django-prosjekt 
og kjører populate-scriptet (se instruksjoner for loakalt oppsett).
Om du er opptatt av sikkerhet kan det være en god idé å deaktivere dummy-brukerne 
som ble generert og å endre passordet på 'admin'-brukeren.
Merk at populate-scriptet sletter all data fra databasen før det oppretter dummy-data,
det er derfor viktig at du i itsBooking/settings.py setter 'DEBUG = FALSE'.  
Dette vil stoppe debug-scriptet fra å kunne bli kjørt fra nettsiden. 

## Tester
Det er ved skrivende stund skrevet 55 unit-tester for prosjektet. Disse 
tester det meste av eksisterende backend-logikk for større og mindre feil.

For å kjøre testene må du først gjennomføre instruksene for lokalt oppsett.
Du kan så gå inn i terminalen og skrive 'python manage.py test'.
Om en ønsker å teste en spesifikk modul ('app' i django)
kan en legge til modulnavnet bakerst. (eks. 'python manage.py test booking)

For å se en nøyaktig beskrivelse av kodedekningen til prosjektet kan du, etter å ha fulgt
instruksene for lokalt oppset, kjøre følgende kommandoer i terminalen:
1. coverage run --source='.' manage.py test
2. coverage html

Det skal da genereres en ny mappe fylt med html-filer som gir en komplett oversikt 
over dekingsgraden til testene, der det er mulig å se hvilke linjer som testes og ikke testes.
For å se dette kan en å åpne en av disse html-filene i en nettleser
og navigere rundt. Vær klar over at det kan ta litt tid før stylingen lastes inn. 



## Brukermanual
Se [wiki-sidene](https://gitlab.stud.iie.ntnu.no/programvareutvikling-v19/gruppe-60/wikis/Brukermanual) 