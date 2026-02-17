import io
import json
import calendar
import streamlit as st
import pandas as pd
import calendar

from datetime import date
from dateutil.relativedelta import relativedelta

from reportlab.lib.pagesizes import landscape, letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch

from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode

if "selected_cells" not in st.session_state:
    st.session_state.selected_cells = {}

if "deselected_cells" not in st.session_state:
    st.session_state.deselected_cells = {}

if "auto_selected_cells" not in st.session_state:
    st.session_state.auto_selected_cells = {}

if "auto_deselected_cells" not in st.session_state:
    st.session_state.auto_deselected_cells = {}

if "selectable_cells" not in st.session_state:
    st.session_state.selectable_cells = {}

if "all_calendars" not in st.session_state:
    st.session_state.all_calendars = {}

if "reset_counter" not in st.session_state:
    st.session_state.reset_counter = 0

if "last_start_date" not in st.session_state:
    st.session_state.last_start_date = None

session_states = [st.session_state.selected_cells, st.session_state.deselected_cells,
    st.session_state.auto_selected_cells, st.session_state.auto_deselected_cells, st.session_state.selectable_cells,
    st.session_state.all_calendars, st.session_state.last_start_date]

cell_states = session_states[:5]

selected_cells, deselected_cells, auto_selected_cells, auto_deselected_cells, selectable_cells = st.session_state.selected_cells, st.session_state.deselected_cells, st.session_state.auto_selected_cells, st.session_state.auto_deselected_cells, st.session_state.selectable_cells  
all_calendars = st.session_state.all_calendars

start_date = st.date_input("Select starting date:", value=date.today(), format="MM/DD/YYYY")
name_of_case = st.text_input("Name of case:")
prepared_by = st.text_input("Prepared by:")  

def clear_session():
    st.session_state.reset_counter += 1
    for i in cell_states:
        i.clear()
    st.session_state.last_start_date = None
    st.rerun()

print("current start",start_date)
print("previous start",st.session_state.last_start_date)

if st.session_state.last_start_date is None:
    st.session_state.last_start_date = start_date
elif start_date != st.session_state.last_start_date:
    print("rerunning")
    clear_session()
    st.session_state.last_start_date = start_date

months = [start_date + relativedelta(months=i) for i in range(25)]
calendar.setfirstweekday(calendar.SUNDAY)

cell_style_jscode = JsCode("""
function(params) {
    console.log("style");
    console.log(params);
    console.log(params.context.selectedCells);
    const tableId = params.context.tableId;
    const cellId = tableId + "|" + params.rowIndex + "|" + params.column.colId;
    const selectableCells = params.context.selectableCells;
    const selectedBackgroundColor = "#81d4fa";
    const unselectedBackgroundColor = "#FFFFFF";
    const selectableTextColor = "#000000";
    const unselectableTextColor = "#CCCCCC";
    const borderColor = "#000000";
    
                           
    if (!window.selectedCells) { window.selectedCells = params.context.selectedCells; }
    //if (!window.selectedCells[tableId]) { window.selectedCells[tableId] = params.context.deselectedCells; }
    if (!window.deselectedCells) { window.deselectedCells = params.context.deselectedCells; }
    //if (!window.deselectedCells[tableId]) { window.deselectedCells[tableId] = {}; }
    if (!window.autoSelectedCells) { window.autoSelectedCells = params.context.autoSelectedCells; }
    //if (!window.autoSelectedCells[tableId]) { window.autoSelectedCells[tableId] = {}; }
    if (!window.autoDeselectedCells) { window.autoDeselectedCells = params.context.autoDeselectedCells; }
    //if (!window.autoDeselectedCells[tableId]) { window.autoDeselectedCells[tableId] = {}; }
    
    let selectedCells = window.selectedCells;
    let deselectedCells = window.deselectedCells;
    let autoSelectedCells = window.autoSelectedCells;
    let autoDeselectedCells = window.autoDeselectedCells;
                           
    style = {border: borderColor, textAlign: 'center', backgroundColor: unselectedBackgroundColor, 
        color: selectableTextColor, borderRight: "1px solid "+borderColor,
        borderLeft: "1px solid " + borderColor,};
    if(selectedCells[cellId]) {
        style["backgroundColor"] = selectedBackgroundColor;
    }
    if (!selectableCells[cellId]) {
        style["cursor"] = "not-allowed";
        style["color"] = unselectableTextColor;
    }
    return style;
}
""")

onCellClickedHandler = JsCode("""
function(params) {
    const tableId = params.context.tableId;
    const selectableCells = params.context.selectableCells;
    console.log("click");
    console.log(params);
    console.log(params.context.selectedCells);
    if (!window.selectedCells) { window.selectedCells = params.context.selectedCells; }
    //if (!window.selectedCells[tableId]) { window.selectedCells[tableId] = params.context.deselectedCells; }
    if (!window.deselectedCells) { window.deselectedCells = params.context.deselectedCells; }
    //if (!window.deselectedCells[tableId]) { window.deselectedCells[tableId] = {}; }
    if (!window.autoSelectedCells) { window.autoSelectedCells = params.context.autoSelectedCells; }
    //if (!window.autoSelectedCells[tableId]) { window.autoSelectedCells[tableId] = {}; }
    if (!window.autoDeselectedCells) { window.autoDeselectedCells = params.context.autoDeselectedCells; }
    //if (!window.autoDeselectedCells[tableId]) { window.autoDeselectedCells[tableId] = {}; }
                              
    
    let selectedCells = window.selectedCells;
    let deselectedCells = window.deselectedCells;
    let autoSelectedCells = window.autoSelectedCells;
    let autoDeselectedCells = window.autoDeselectedCells;
    console.log(selectedCells);

    const cellId = tableId + "|" + params.rowIndex + "|" + params.column.colId;
    if (!selectableCells[cellId]) { return; }
    if(selectedCells[cellId]) {
        console.log("cell is selected");
        delete selectedCells[cellId]; 
        deselectedCells[cellId] = true; 
    }
    else {
        console.log("cell is not already selected");
        selectedCells[cellId] = true;
        delete deselectedCells[cellId]; 
    }

    // Write selection to hidden columns
    console.log("hidden column");
    const firstRow = params.api.getDisplayedRowAtIndex(0);
    if(firstRow) firstRow.setDataValue("_hidden_column", JSON.stringify([selectedCells, deselectedCells]));
    console.log(selectedCells);
    console.log(deselectedCells);
    console.log(firstRow.data["_hidden_column"]);

    params.api.refreshCells({force:true});
}
""")

def month_dataframe(months, idx):
    month_date = months[idx]
    year = month_date.year
    month = month_date.month
    headers = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    table_id = f"grid-{year}-{month}"
    for i in range(len(cell_states)):
        if table_id not in cell_states[i]:
            cell_states[i][table_id] = {}
    
    cal = calendar.Calendar(calendar.SUNDAY).monthdatescalendar(year, month)
    for i in range(len(cal)):
        for j in range(len(cal[i])):
            if cal[i][j].month == month and (cal[i][j] - start_date).days >= 0 and (cal[i][j] - start_date).days <= 730:
                st.session_state.selectable_cells[table_id][f"{table_id}|{i}|{headers[j]}"] = True
            cal[i][j] = cal[i][j].day
    day = cal[-1][-1]
    if day > 7:
        day = 0
    for i in range(6-len(cal)): 
        cal.append([day+7*i+j+1 for j in range(7)]) 
    all_calendars[table_id] = cal
    
    
    df = pd.DataFrame(cal, columns=headers)
    cal = [headers] + cal
    return df, year, month, cal


def render_month(months, idx):
    df, year, month, _ = month_dataframe(months, idx)

    if "_hidden_column" not in df.columns:
        df["_hidden_column"] = ""

    st.markdown(f"### {calendar.month_name[month]} {year}")

    table_id = f"grid-{year}-{month}"

    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_selection(selection_mode="single", use_checkbox=False)
    # Enable multi-cell selection
    gb.configure_grid_options(
        rowHeight=20,
        headerHeight=30,
        suppressRowClickSelection=True,
        onCellClicked = onCellClickedHandler,
        suppressMovable=True,
        context={
            "tableId": table_id,
            "selectedCells": selected_cells[table_id],
            "deselectedCells": deselected_cells[table_id],
            "autoSelectedCells": auto_selected_cells[table_id], 
            "autoDeselectedCells": auto_deselected_cells[table_id],
            "selectableCells": selectable_cells[table_id],
            },
    )

    # Style all columns
    for col in df.columns:
        if col != "_hidden_column":
            gb.configure_column(
                col,
                headerComponentParams={
                'template': '<div style="text-align: center; width: 100%; height:100;">' +
                        col +
                        '</div>'
                },
                cellStyle=cell_style_jscode,
                editable=False,
                suppressMovable=True,
                sortable=False,
                filter=False,
                suppressMenu=True, 
            )
    gb.configure_column("_hidden_column", hide=True, editable=True, width=0, minWidth=0, maxWidth=0)

    grid = AgGrid(
        df,
        gridOptions=gb.build(),
        update_mode=GridUpdateMode.VALUE_CHANGED,
        allow_unsafe_jscode=True,
        height=153,
        key=f"{table_id}-{st.session_state.reset_counter}",
    )
    
    data = grid["data"]
    
    val = data.iloc[0]["_hidden_column"]
    
    if val:
        [selected, deselected] = json.loads(val)
        st.session_state.selected_cells[table_id] = selected
        st.session_state.deselected_cells[table_id] = deselected
    else:
        st.session_state.selected_cells[table_id] = {}
        st.session_state.deselected_cells[table_id] = {}
    return selected_cells

def selected_per_year(total_selected):
    flattened_selectable = [i for j in selectable_cells.values() for i in j]
    flattened_selected = [i for j in total_selected.values() for i in j]
    year1 = 0
    year2 = 0
    weekdays = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    weekdays_to_day = {weekdays[i]:i for i in range(7)}
    for i in flattened_selected:
        [table_id, r, c] = i.split("|")
        r = int(r)+1
        c = weekdays_to_day[c]
        [year, month] = table_id.split('-')[1:]
        year = int(year)
        month = int(month)
        selected_date = date(year=year, month=month,day=all_calendars[table_id][r-1][c])
        if (selected_date - start_date).days < 365:
            year1 += 1
        else:
            year2 += 1
    return year1, year2

# Draw one page of calendars
def draw_calendar_page(c, start_date, num_months, selected_cells, show_title=False):
    width, height = landscape(letter)
    margin = inch
    month_width = (width - 2*margin)/4*28/31
    month_height = (height - 2*margin)/4*28/31
    start_x = margin
    start_y = height - margin

    # Title and author
    if show_title:
        year1, year2 = selected_per_year(selected_cells)
        total = sum([len(v) for v in selected_cells.values()])
        c.setFont("Times-Bold", 24)
        c.drawString(start_x, start_y - 0.1*inch, "Parenting Time Calendar")
        c.setFont("Times-Roman", 12)
        c.drawString(start_x, start_y - 0.5*inch, f"Case: {name_of_case}")
        c.drawString(start_x, start_y - 0.75*inch, f"Prepared by: {prepared_by}")
        c.drawString(width - 3*inch, start_y , f"Total Dates Selected: {total}")
        c.drawString(width - 3*inch, start_y - 0.25*inch, f"Year 1: {year1}")
        c.drawString(width - 3*inch, start_y - 0.5*inch, f"Year 2: {year2}")
        c.drawString(width - 3*inch, start_y - 0.75*inch, f"Yearly Average: {total/2}")
        offset_y = start_y - inch
    else:
        offset_y = start_y

    for i in range(num_months):
        month_date = start_date + relativedelta(months=i)
        year, month = month_date.year, month_date.month
        table_id = f"grid-{year}-{month}"
        _,_,_,matrix = month_dataframe(months,i)

        col_idx = i % 4
        row_idx = i // 4
        x0 = start_x + col_idx * month_width*31/28
        y0 = offset_y - row_idx * month_height*31/28

        # Month title
        c.setFont("Times-Bold", 12)
        c.drawCentredString(x0 + month_width/2, y0 - 0.2*inch, f"{calendar.month_name[month]} {year}")

        # Draw table
        cell_width = month_width / 7
        cell_height = (month_height - 0.3*inch)/len(matrix)
        for r, week in enumerate(matrix):
            for c_idx, day in enumerate(week):
                cell_x = x0 + c_idx*cell_width
                cell_y = y0 - 0.3*inch - r*cell_height
                cell_id = f"{table_id}|{r-1}|{matrix[0][c_idx]}"
                
                if r > 0 and cell_id in selected_cells.get(table_id, {}):
                    c.setFillColor(colors.lightblue)
                    c.rect(cell_x, cell_y - cell_height, cell_width, cell_height, fill=1, stroke=0)
                    c.setFillColor(colors.black)
                elif r > 0 and cell_id not in selectable_cells.get(table_id, {}):
                    c.setFillColor(colors.lightgrey)
                else:
                    c.setFillColor(colors.black)
                    
                # Draw borders
                c.setStrokeColor(colors.black)
                c.rect(cell_x, cell_y - cell_height, cell_width, cell_height, fill=0)
                # Draw text
                if r == 0:
                    text = str(day)
                    c.setFont("Times-Bold", 8)
                else:
                    text = str(day)
                    c.setFont("Times-Roman", 8)
                c.drawCentredString(cell_x + cell_width/2, cell_y - cell_height + 2, text)
                c.setFillColor(colors.black)

def generate_pdf(start_date):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(letter))

    # Front page: first 12 months with title
    draw_calendar_page(c, start_date, 12, selected_cells, show_title=True)
    c.showPage()

    # Back page: last 13 months, no title
    draw_calendar_page(c, start_date + relativedelta(months=12), 13, selected_cells, show_title=False)
    c.showPage()

    c.save()

    buffer.seek(0)
    return buffer.getvalue()

st.set_page_config(layout="wide")
st.title("📅 Calendar Selector")


st.download_button(
    label="Download PDF",
    data=generate_pdf(start_date),
    file_name="calendar_selection.pdf",
    icon=":material/picture_as_pdf:",
)

st.markdown("---")

year1, year2 = selected_per_year(selected_cells)
st.write(selected_cells)

t1 = st.markdown(f"### Total Dates Selected: **{sum([len(v) for v in selected_cells.values()])}**")
t2 = st.markdown(f"#### Year 1: **{year1}**")
t3 = st.markdown(f"#### Year 2: **{year2}**")
t4 = st.markdown(f"#### Yearly Average: **{sum([len(v) for v in selected_cells.values()])/2}**")

st.markdown("---")

# Clear button
if st.button("Clear All Selections"):
    clear_session()

months_per_row = 4
for i in range(0, len(months), months_per_row):
    row = st.columns(months_per_row)
    for j in range(months_per_row):
        if i + j < len(months):
            with row[j]:
                selected_cells = render_month(months, i + j)


year1, year2 = selected_per_year(selected_cells)
st.write(selected_cells)

t1.markdown(f"### Total Dates Selected: **{sum([len(v) for v in selected_cells.values()])}**")
t2.markdown(f"#### Year 1: **{year1}**")
t3.markdown(f"#### Year 2: **{year2}**")
t4.markdown(f"#### Yearly Average: **{sum([len(v) for v in selected_cells.values()])/2}**")





