# Gratis DakScan Vlaanderen — smartphone MVP

## Wat dit prototype doet
- Adres zoeken via Nominatim / OpenStreetMap.
- Gebouwcontouren in de buurt ophalen via Overpass.
- Contour naar Belgisch Lambert 72 (EPSG:31370) projecteren en oppervlakte berekenen.
- Indicatieve hellingscorrectie: footprint / cos(helling).
- Schematische 3D-weergave.
- PDF-rapport met beperkingen en bronvermelding.

## Eerlijk over nauwkeurigheid
Dit is nadrukkelijk **geen volautomatische dakvlakken-detectie**. De OSM-contour kan ontbreken of afwijken van de dakrand. Dakhelling is invoer, geen automatische meting. De 3D-weergave is schematisch. Gebruik het resultaat niet als definitieve maatstaat voor renovatiebestellingen zonder verificatie. Voor een echte Spotable-achtige engine moeten officiële GRB-gebouwcontouren en DHMV/LiDAR-gegevens geïntegreerd en gevalideerd worden.

Daktype schilddak en 40° zijn vooraf ingevuld op basis van de opgegeven casus. Controleer de adresmatch en selecteer het juiste gebouw.

## Lokaal starten
Installeer Python 3.11/3.12, pak de ZIP uit en open een terminal in deze map.

Windows:
```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```
macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Gebruiken op smartphone
Op hetzelfde wifi-netwerk als de computer:
```bash
streamlit run app.py --server.address 0.0.0.0
```
Open op de smartphone `http://IP-ADRES-VAN-COMPUTER:8501`.

Gratis online hosten: zet de bestanden in een GitHub-repository en deploy via https://share.streamlit.io/ met `app.py` als entrypoint. Streamlit Community Cloud is gratis, maar heeft gebruiks- en resourcebeperkingen en de app wordt online publiek toegankelijk als de repository/app publiek staat.

## Bronnen
- OpenStreetMap: https://www.openstreetmap.org/copyright
- Nominatim-gebruiksbeleid: https://operations.osmfoundation.org/policies/nominatim/
- Overpass API: https://overpass-api.de/
- Officiële GRB-webdiensten (gratis open data; nog niet rechtstreeks aangesloten in deze MVP): https://www.vlaanderen.be/digitaal-vlaanderen/onze-diensten-en-platformen/basiskaart-vlaanderen-grb/grb-webdiensten
- Streamlit deployment: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy

## Volgende technische stap
Voeg GRB OGC API Features toe om de juiste officiële gebouwcontour op te halen. Koppel vervolgens geschikte DHMV/LiDAR-punten, reconstrueer dakvlakken, valideer tegen orthofoto en toon per vlak bron, helling en onzekerheid.
