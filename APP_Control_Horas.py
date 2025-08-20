import streamlit as st
import pandas as pd
import datetime
import json
import os
from typing import Dict, List, Optional

class TimeTracker:
    def __init__(self):
        self.data_file = "work_hours.json"
        self.load_data()
    
    def load_data(self):
        """Cargar datos desde el archivo JSON"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            except:
                self.data = {}
        else:
            self.data = {}
    
    def save_data(self):
        """Guardar datos en el archivo JSON"""
        with open(self.data_file, 'w') as f:
            json.dump(self.data, f, indent=4)
    
    def register_entry(self, date: str, entry_time: str):
        """Registrar hora de entrada"""
        if date not in self.data:
            self.data[date] = {"entry": entry_time, "exit": None, "notes": ""}
        else:
            self.data[date]["entry"] = entry_time
        self.save_data()
    
    def register_exit(self, date: str, exit_time: str, notes: str = ""):
        """Registrar hora de salida"""
        if date not in self.data:
            self.data[date] = {"entry": None, "exit": exit_time, "notes": notes}
        else:
            self.data[date]["exit"] = exit_time
            self.data[date]["notes"] = notes
        self.save_data()
    
    def calculate_daily_hours(self, date: str) -> Optional[float]:
        """Calcular horas trabajadas en un día"""
        if date in self.data and self.data[date]["entry"] and self.data[date]["exit"]:
            entry = datetime.datetime.strptime(self.data[date]["entry"], "%H:%M")
            exit = datetime.datetime.strptime(self.data[date]["exit"], "%H:%M")
            
            # Manejar casos donde la salida es después de medianoche
            if exit < entry:
                exit += datetime.timedelta(days=1)
            
            hours_worked = (exit - entry).total_seconds() / 3600
            return round(hours_worked, 2)
        return None
    
    def get_weekly_summary(self, week_start: datetime.date) -> Dict:
        """Obtener resumen semanal"""
        week_data = {}
        total_hours = 0
        days_worked = 0
        
        for i in range(7):
            current_date = week_start + datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            if date_str in self.data:
                hours = self.calculate_daily_hours(date_str)
                if hours:
                    week_data[date_str] = {
                        "entry": self.data[date_str]["entry"],
                        "exit": self.data[date_str]["exit"],
                        "hours": hours,
                        "notes": self.data[date_str]["notes"]
                    }
                    total_hours += hours
                    days_worked += 1
        
        return {
            "days": week_data,
            "total_hours": round(total_hours, 2),
            "days_worked": days_worked,
            "average_per_day": round(total_hours / days_worked, 2) if days_worked > 0 else 0
        }

def main():
    st.set_page_config(
        page_title="Control de Horas de Trabajo",
        page_icon="⏰",
        layout="wide"
    )
    
    # Inicializar el tracker
    tracker = TimeTracker()
    
    st.title("⏰ Control de Horas de Trabajo")
    st.markdown("---")
    
    # Sidebar para navegación
    st.sidebar.title("Navegación")
    page = st.sidebar.radio("Selecciona una página:", 
                           ["Registrar Horas", "Ver Resumen Semanal", "Historial Completo"])
    
    # Obtener fecha actual
    today = datetime.date.today()
    current_week_start = today - datetime.timedelta(days=today.weekday())
    
    if page == "Registrar Horas":
        st.header("📝 Registrar Horas")
        
        col1, col2 = st.columns(2)
        
        with col1:
            selected_date = st.date_input("Selecciona la fecha:", today)
            date_str = selected_date.strftime("%Y-%m-%d")
            
            # Mostrar información del día seleccionado
            if date_str in tracker.data:
                st.info(f"**Registro existente para {selected_date.strftime('%d/%m/%Y')}:**")
                if tracker.data[date_str]["entry"]:
                    st.write(f"🟢 Entrada: {tracker.data[date_str]['entry']}")
                if tracker.data[date_str]["exit"]:
                    st.write(f"🔴 Salida: {tracker.data[date_str]['exit']}")
                if tracker.data[date_str]["notes"]:
                    st.write(f"📝 Notas: {tracker.data[date_str]['notes']}")
            
        with col2:
            # Formulario para registrar entrada/salida
            with st.form("time_form"):
                entry_time = st.time_input("Hora de entrada:", 
                                         value=datetime.time(9, 0),
                                         disabled=date_str in tracker.data and tracker.data[date_str]["entry"])
                
                exit_time = st.time_input("Hora de salida:",
                                        value=datetime.time(18, 0),
                                        disabled=date_str in tracker.data and tracker.data[date_str]["exit"])
                
                notes = st.text_area("Notas del día:", 
                                   value=tracker.data[date_str].get("notes", "") if date_str in tracker.data else "")
                
                col1, col2 = st.columns(2)
                with col1:
                    register_entry = st.form_submit_button("🟢 Registrar Entrada")
                with col2:
                    register_exit = st.form_submit_button("🔴 Registrar Salida")
                
                if register_entry:
                    tracker.register_entry(date_str, entry_time.strftime("%H:%M"))
                    st.success(f"✅ Entrada registrada: {entry_time.strftime('%H:%M')}")
                
                if register_exit:
                    tracker.register_exit(date_str, exit_time.strftime("%H:%M"), notes)
                    hours_worked = tracker.calculate_daily_hours(date_str)
                    st.success(f"✅ Salida registrada: {exit_time.strftime('%H:%M')}")
                    if hours_worked:
                        st.info(f"⏱️ Horas trabajadas: {hours_worked} horas")
    
    elif page == "Ver Resumen Semanal":
        st.header("📊 Resumen Semanal")
        
        # Selector de semana
        week_offset = st.slider("Selecciona la semana:", -4, 4, 0)
        selected_week_start = current_week_start + datetime.timedelta(weeks=week_offset)
        
        weekly_summary = tracker.get_weekly_summary(selected_week_start)
        
        # Mostrar métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Horas", f"{weekly_summary['total_hours']}h")
        with col2:
            st.metric("Días Trabajados", weekly_summary['days_worked'])
        with col3:
            st.metric("Promedio por Día", f"{weekly_summary['average_per_day']}h")
        with col4:
            remaining_hours = max(0, 40 - weekly_summary['total_hours'])
            st.metric("Horas Restantes (40h)", f"{remaining_hours}h")
        
        # Tabla detallada
        st.subheader("Detalle de la Semana")
        week_days = []
        for i in range(7):
            day_date = selected_week_start + datetime.timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            
            day_name = day_date.strftime("%A")
            date_display = day_date.strftime("%d/%m/%Y")
            
            if day_str in weekly_summary['days']:
                day_data = weekly_summary['days'][day_str]
                week_days.append({
                    "Día": f"{day_name} ({date_display})",
                    "Entrada": day_data['entry'],
                    "Salida": day_data['exit'],
                    "Horas": f"{day_data['hours']}h",
                    "Notas": day_data['notes']
                })
            else:
                week_days.append({
                    "Día": f"{day_name} ({date_display})",
                    "Entrada": "-",
                    "Salida": "-",
                    "Horas": "-",
                    "Notas": "-"
                })
        
        df = pd.DataFrame(week_days)
        st.dataframe(df, use_container_width=True)
        
        # Gráfico de horas por día
        if weekly_summary['days_worked'] > 0:
            st.subheader("Distribución de Horas")
            chart_data = []
            for day_str, day_data in weekly_summary['days'].items():
                day_date = datetime.datetime.strptime(day_str, "%Y-%m-%d")
                chart_data.append({
                    "Día": day_date.strftime("%a %d/%m"),
                    "Horas": day_data['hours']
                })
            
            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                st.bar_chart(chart_df.set_index("Día"))
    
    elif page == "Historial Completo":
        st.header("📋 Historial Completo")
        
        # Convertir datos a DataFrame para mejor visualización
        records = []
        for date_str, data in tracker.data.items():
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            hours = tracker.calculate_daily_hours(date_str)
            
            records.append({
                "Fecha": date_obj.strftime("%d/%m/%Y"),
                "Día": date_obj.strftime("%A"),
                "Entrada": data.get("entry", "-"),
                "Salida": data.get("exit", "-"),
                "Horas": f"{hours}h" if hours else "-",
                "Notas": data.get("notes", "")
            })
        
        if records:
            df = pd.DataFrame(records)
            df = df.sort_values("Fecha", ascending=False)
            
            # Filtros
            col1, col2 = st.columns(2)
            with col1:
                filter_days = st.multiselect("Filtrar por días:", 
                                           options=sorted(set(df["Día"])),
                                           default=[])
            with col2:
                min_hours = st.slider("Mínimo horas:", 0.0, 12.0, 0.0, 0.5)
            
            # Aplicar filtros
            filtered_df = df.copy()
            if filter_days:
                filtered_df = filtered_df[filtered_df["Día"].isin(filter_days)]
            
            # Convertir horas a numérico para filtrar
            def extract_hours(x):
                try:
                    return float(x.replace('h', '')) if x != '-' else 0
                except:
                    return 0
            
            filtered_df["Horas_num"] = filtered_df["Horas"].apply(extract_hours)
            filtered_df = filtered_df[filtered_df["Horas_num"] >= min_hours]
            filtered_df = filtered_df.drop(columns=["Horas_num"])
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # Estadísticas
            total_hours = sum(extract_hours(x) for x in df["Horas"] if x != '-')
            total_days = len([x for x in df["Horas"] if x != '-'])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total de Días Registrados", total_days)
            with col2:
                st.metric("Total de Horas", f"{total_hours:.2f}h")
            with col3:
                st.metric("Promedio General", f"{total_hours/total_days:.2f}h/día" if total_days > 0 else "0h")
            
        else:
            st.info("No hay registros aún. ¡Comienza registrando tus horas!")

if __name__ == "__main__":
    main()
