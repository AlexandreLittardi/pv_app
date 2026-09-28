"""Build the source-audited technical note distributed with the application."""
import io
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from home_reference import FORMULAS
from matplotlib.mathtext import math_to_image
from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate,Paragraph,Spacer,Image as ReportImage,
                                 KeepTogether,PageBreak,HRFlowable)

OUTPUT=ROOT/'docs/technical_note_updated.pdf'
OUTPUT.parent.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('DejaVu','/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVu-Bold','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
styles=getSampleStyleSheet()
styles.add(ParagraphStyle(name='TitleOwn',parent=styles['Title'],fontName='DejaVu-Bold',fontSize=19,
                          leading=24,textColor=colors.HexColor('#18334a'),spaceAfter=15))
styles.add(ParagraphStyle(name='SectionOwn',parent=styles['Heading2'],fontName='DejaVu-Bold',fontSize=13,leading=18,
                          spaceBefore=16,spaceAfter=8,textColor=colors.HexColor('#17445d')))
styles.add(ParagraphStyle(name='BodyOwn',parent=styles['BodyText'],fontName='DejaVu',fontSize=9.3,leading=14,spaceAfter=8))
styles.add(ParagraphStyle(name='NoteOwn',parent=styles['BodyText'],fontName='DejaVu',fontSize=8.4,leading=12,
                          textColor=colors.HexColor('#526576'),spaceAfter=8))
styles.add(ParagraphStyle(name='SmallOwn',parent=styles['BodyText'],fontName='DejaVu',fontSize=7.7,leading=11,spaceAfter=6))
story=[]
def para(text,style='BodyOwn'):
    from xml.sax.saxutils import escape
    story.append(Paragraph(escape(text),styles[style]))
para('Photovoltaic layout, shading and storage | Models and formulas','TitleOwn')
para('Technical note revised for the PV Layout application, 28 September 2026. Based on the mathematical appendix by Alexandre Littardi, 25 September 2026; revised against the current source code.','NoteOwn')
story.append(HRFlowable(width='100%',thickness=1,color=colors.HexColor('#c8dae6')))
para('What was corrected','SectionOwn')
for point in [
    'Dated simulations now use their actual calendar year and 365 or 366 days, rather than a fixed 2024/365 assumption. The undated Shadow preview still uses representative year 2024.',
    'The earlier note only described clear-sky shading. The annual Energy/BESS simulation can use imported historical weather; a chosen weather source is recorded with the results.',
    'The solar-to-module relation is a simplified irradiance and linear temperature model. It does not solve a single-diode circuit or reproduce a complete NOCT/SAM thermal model.',
    'DC voltage drop uses the lengths of both conductor runs, A+B. Replacing A+B by 2L is valid only when the two runs have equal length.',
    'The original MPPT voltage interval described a spread of string voltages, not electrical compatibility. Parallel strings of unequal lengths are flagged for review.',
    'The updated note includes hourly direct PV use, shared BESS charge/discharge power limits, SOC constraints, export limit, curtailed energy and net grid cost.',
    'DC conductor sections, protective devices, cold-temperature voltage, cable thermal rating, battery expansion and grid approval still require certified equipment information and engineering review.',
]:para('• '+point,'SmallOwn')
para('Reading the equations','SectionOwn')
para('The expressions below describe the code paths used by this version. A missing weather profile selects the clear-sky estimate. Units, direction conventions and limits must be read with each equation. The guides in Home show the same material in an interactive form.','BodyOwn')
for title,description,items in FORMULAS:
    para(title,'SectionOwn');para(description)
    for expression,explanation in items:
        buffer=io.BytesIO();math_to_image('$'+expression+'$',buffer,dpi=165,format='png',color='#18334a')
        buffer.seek(0);raster=Image.open(buffer)
        w=min(171*mm,raster.width/165*72);h=raster.height/165*72*w/(raster.width/165*72)
        equation=ReportImage(buffer,width=w,height=h)
        story.append(KeepTogether([Spacer(1,5),equation,Spacer(1,5),Paragraph(explanation,styles['NoteOwn'])]))
story.append(PageBreak())
para('Traceability and limits','SectionOwn')
for line in [
    'Solar geometry and irradiance: mixins/shadow_energy.py; obstacle footprint, clipping and area: mixins/shadow_geometry.py; panel grid: mixins/zone_tools.py.',
    'String and MPPT STC values: mixins/diagram_tools.py and detailed_electrical.py; network routes and two DC terminals: mixins/cable_network.py and mixins/two_pole_cables.py; voltage-drop recommendation: mixins/notes_tools.py.',
    'Hourly generation: self_consumption.py; one/two BESS dispatch: battery_dispatch.py; avoided purchases, export revenue and payback: energy_economics.py.',
    'The roof shadow model uses a square obstacle footprint and separate zone heights, not an as-built mesh of a lattice tower. String mismatch, diodes, snow, wind, bifacial gain and all network protection settings are outside this simulation.',
    'Public reference: NOAA General Solar Position Calculations, https://gml.noaa.gov/grad/solcalc/solareqns.PDF (366-day leap-year denominator).',
    'Public reference: Sandia PV Performance Modeling Collaborative, NOCT Cell Temperature, https://pvpmc.sandia.gov/modeling-guide/2-dc-module-iv/cell-temperature/noct-cell-temperature/ (the application uses a simplified ambient-temperature estimate).',
]:para('• '+line,'SmallOwn')
para('Interpretation for the 516-module project','SectionOwn')
for item in [
    'The supplied 516-module reference represents 371.52 kWp of nominal DC modules assigned to three 125 kVA hybrid inverters and thirty-one strings. The stored annual clear-sky calculation is a scenario, not measured PV yield; historic weather and load data must be checked for matching dates and time conventions.',
    'One MC-L522 has two battery clusters connected to two inverter BAT ports in the available DEYE drawing. The third hybrid is dedicated to PV. An additional MC-L522 cabinet must not be represented as approved parallel DC wiring until a manufacturer-approved extension drawing is available.',
    'The requested 300 kW export setting is a scenario limit for the hourly dispatch. The 507 kW existing contract is a different quantity. Neither value by itself documents a granted injection authorization or a tested grid-interface protection.',
    'Cable paths are estimates until traced on site. A valid A+B record includes two conductor routes, roof height difference and configured reserve. Conductor sizing from DC voltage drop does not substitute for ampacity, short-circuit, thermal and protective coordination studies.',
    'Shadow preview and dated shadow studies accept a manually supplied UTC offset; the undated preview uses representative year 2024. Dated shadow simulations use the real calendar year. The annual simulation derives hourly offsets from Europe/Rome and its timestamp. Clear-sky module temperature assumes 20°C ambient; imported weather supplies hourly ambient temperature and plane-of-array irradiance for a single module orientation.',
]:para('• '+item,'BodyOwn')

def footer(canvas,document):
    canvas.setFont('DejaVu',8);canvas.setFillColor(colors.HexColor('#5a6a77'))
    canvas.drawString(19*mm,14*mm,'PV Layout | revised technical note | preliminary engineering model')
    canvas.drawRightString(191*mm,14*mm,str(document.page))

SimpleDocTemplate(str(OUTPUT),pagesize=A4,rightMargin=19*mm,leftMargin=19*mm,
                  topMargin=19*mm,bottomMargin=22*mm,title='PV Layout | Revised technical note',
                  author='Source-audited revision of Alexandre Littardi technical appendix').build(story,onFirstPage=footer,onLaterPages=footer)
print(OUTPUT)
