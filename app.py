import io, math, time
import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from shapely.geometry import Polygon
from shapely.ops import transform
from pyproj import Transformer
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Gratis DakScan Vlaanderen", page_icon="🏠", layout="centered")
st.title("🏠 Gratis DakScan Vlaanderen")
st.caption("Mobiele eerste versie · gratis diensten · transparante berekeningen")
st.warning("Dit prototype meet niet automatisch afzonderlijke dakvlakken. Een gebouwcontour is geen dakmeting. De 3D-weergave is schematisch en mag niet als maatvaste reconstructie worden gebruikt.")

address = st.text_input("Adres", "Baan naar Bree 126, 3990 Peer, België")
c1,c2=st.columns(2)
with c1: roof_type=st.selectbox("Daktype",["Schilddak","Zadeldak","Plat dak","Onbekend"],0)
with c2: pitch=st.number_input("Dakhelling (graden)",0.0,70.0,40.0,1.0)
st.caption("Schilddak en 40° zijn vooraf ingevuld op basis van jouw eerdere opgave; ze zijn niet automatisch gemeten.")
go=st.button("Zoek gebouw en bereken",type="primary",use_container_width=True)

def get_json(url, params=None):
    r=requests.get(url,params=params,timeout=30,headers={"User-Agent":"GratisDakScanVlaanderen/0.1 contact: open-data prototype"})
    r.raise_for_status()
    return r.json()
def geocode(q):
    return get_json("https://nominatim.openstreetmap.org/search",{"q":q,"format":"jsonv2","limit":5,"countrycodes":"be"})
def buildings(lat,lon):
    query='[out:json][timeout:25];(way["building"](around:100,'+str(lat)+','+str(lon)+'););out geom;'
    r=requests.post("https://overpass-api.de/api/interpreter",data={"data":query},timeout=40,headers={"User-Agent":"GratisDakScanVlaanderen/0.1"})
    r.raise_for_status()
    return r.json().get("elements",[])
def poly_for(el):
    coords=[(p["lon"],p["lat"]) for p in el.get("geometry",[])]
    if len(coords)>=4:
        p=Polygon(coords)
        if p.is_valid and p.area>0: return p
    return None
def project(p):
    tr=Transformer.from_crs("EPSG:4326","EPSG:31370",always_xy=True)
    return transform(tr.transform,p)
def pdf_bytes(d):
    b=io.BytesIO(); doc=SimpleDocTemplate(b,pagesize=A4); styles=getSampleStyleSheet()
    story=[Paragraph("DakScan Vlaanderen — voorlopig rapport",styles["Title"]),Spacer(1,12)]
    for line in [
        "Adres: "+d["adres"],"Datum: "+time.strftime("%d-%m-%Y"),
        "Bron gebouwcontour: OpenStreetMap / Overpass; niet geverifieerd tegen GRB.",
        "Daktype (opgegeven): "+d["type"],f"helling (opgegeven): {d['pitch']:.1f} graden",
        f"Horizontale footprint: {d['footprint']:.2f} m²",
        f"Rekenfactor: {d['factor']:.4f}" if d["factor"] else "Rekenfactor: niet van toepassing",
        f"Indicatieve schuine dakoppervlakte: {d['roof']:.2f} m²" if d["roof"] is not None else "Schuine oppervlakte niet berekend",
        "Beperkingen: OSM-contour kan ontbreken, verouderd zijn of afwijken van de dakrand. Dakhelling is invoer, geen automatische meting. De formule footprint/cos(helling) is slechts indicatief en veronderstelt een representatieve helling. Overstekken, dakkapellen, aanbouwen en verschillende dakvlakken kunnen afwijken.",
        "Geen automatische AI-detectie van dakvlakken of echte 3D-reconstructie uitgevoerd.",
        "Bronvermelding: © OpenStreetMap contributors (ODbL)."
    ]:
        story.extend([Paragraph(line.replace("&","&amp;"),styles["BodyText"]),Spacer(1,7)])
    doc.build(story); b.seek(0); return b.getvalue()

if go:
    try:
        with st.spinner("Adres zoeken…"): results=geocode(address)
        if not results:
            st.error("Geen adresmatch gevonden. Controleer straat, nummer, postcode en gemeente."); st.stop()
        opts=[x["display_name"] for x in results]
        chosen=results[st.selectbox("Kies adresmatch",range(len(opts)),format_func=lambda i:opts[i])]
        lat,lon=float(chosen["lat"]),float(chosen["lon"])
        st.write(f"Geocode-punt: {lat:.6f}, {lon:.6f}. Dit is niet noodzakelijk het middelpunt van het dak.")
        with st.spinner("Gebouwen in de omgeving ophalen…"): els=buildings(lat,lon)
        items=[]
        tr=Transformer.from_crs("EPSG:4326","EPSG:31370",always_xy=True)
        from shapely.geometry import Point
        point=transform(tr.transform,Point(lon,lat))
        for el in els:
            p=poly_for(el)
            if p:
                pm=project(p); items.append((pm.distance(point),el,p,pm))
        if not items:
            st.error("Geen OSM-gebouwcontour gevonden binnen 100 m. De volgende versie moet de officiële GRB-service toevoegen."); st.stop()
        items.sort(key=lambda x:x[0])
        labels=[f"OSM {x[1]['id']} · afstand {x[0]:.1f} m · contour {x[3].area:.1f} m² · {x[1].get('tags',{}).get('building','gebouw')}" for x in items[:10]]
        idx=st.selectbox("Selecteer het juiste gebouw — controleer op kaart/luchtfoto",range(len(labels)),format_func=lambda i:labels[i])
        dist,el,p,pm=items[idx]; footprint=float(pm.area)
        factor=1/math.cos(math.radians(pitch)) if pitch>0 else None
        roof=footprint*factor if factor else None
        st.subheader("Resultaten")
        a,b=st.columns(2)
        a.metric("Horizontale gebouwcontour",f"{footprint:.1f} m²")
        b.metric("Indicatieve schuine oppervlakte",f"{roof:.1f} m²" if roof is not None else "Niet berekend")
        st.caption("Dit is een OSM-contour, geen officiële GRB-meting. Controleer of de gekozen contour het juiste gebouw is.")
        st.map(pd.DataFrame({"lat":[lat],"lon":[lon]}),zoom=17)
        st.write("OSM-object:",el["type"],el["id"],"· tags:",el.get("tags",{}))
        with st.expander("Contourcoördinaten"):
            st.json({"vertices":len(p.exterior.coords),"coordinates_lon_lat":[[round(x,7),round(y,7)] for x,y in p.exterior.coords]})
        st.subheader("Schematische 3D-weergave")
        minx,miny,maxx,maxy=pm.bounds
        h=max(3.0,math.sqrt(footprint)*0.25); ridge=h+math.tan(math.radians(pitch))*min((maxx-minx)/2,(maxy-miny)/2)
        fig=go.Figure()
        fig.add_trace(go.Scatter3d(x=[minx,maxx,maxx,minx,minx],y=[miny,miny,maxy,maxy,miny],z=[h]*5,mode="lines",name="schematische dakrand"))
        fig.add_trace(go.Scatter3d(x=[(minx+maxx)/2],y=[(miny+maxy)/2],z=[ridge],mode="markers+text",text=["schematisch hoogste punt"],textposition="top center",name="geen gemeten nok"))
        fig.update_layout(scene=dict(xaxis_title="Lambert 72 X (m)",yaxis_title="Lambert 72 Y (m)",zaxis_title="schematische hoogte (m)",aspectmode="data"),height=400,margin=dict(l=0,r=0,t=20,b=0))
        st.plotly_chart(fig,use_container_width=True)
        st.info("Hoogtes en dakvlakken in deze visualisatie zijn niet gemeten. Niet gebruiken voor uitvoering of bestelling.")
        report={"adres":address,"type":roof_type,"pitch":pitch,"footprint":footprint,"factor":factor,"roof":roof}
        st.download_button("Download PDF-rapport",pdf_bytes(report),"dakscan_voorlopig_rapport.pdf","application/pdf",use_container_width=True)
    except requests.HTTPError as e: st.error(f"Openbare databron gaf HTTP-fout: {e}. Probeer later opnieuw; publieke diensten kunnen limieten toepassen.")
    except requests.RequestException as e: st.error(f"Netwerkfout: {e}")
    except Exception as e: st.error(f"Fout tijdens verwerking: {e}")
else:
    st.markdown("### Eerste versie")
    st.write("Adres zoeken · OSM-gebouwcontour ophalen · oppervlakte in Lambert 72 berekenen · indicatieve hellingscorrectie · schematische 3D · PDF.")
    st.write("Nog niet inbegrepen: automatische GRB-identificatie, automatische LiDAR-dakvlakreconstructie of automatisch gemeten dakhelling.")
