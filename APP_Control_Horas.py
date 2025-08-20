import streamlit as st
import pandas as pd
import datetime
import json
import os

# Configuración de la página
st.set_page_config(
    page_title="Control de Horas de Trabajo",
    page_icon="⏰",
    layout="wide"
)

class TimeTracker:
    def __init__(self):
        self.data_file = "work_hours.json"
        self.load_data()
    
    def load_data(self):
        """Cargar datos desde el archivo JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    self.data = json.load(f)
            else:
                self.data = {}
        except:
            self.data = {}
    
    def save_data(self):
        """Guardar datos en el archivo JSON"""
        try:
            with open(self.data_file, 'w') as f:
                json.dump(self.data, f, indent=4)
        except:
            st.error("Error al guardar los datos")
    
    def register_entry(self, date_str, entry_time):
        """Registrar hora de entrada"""
        if date_str not in self.data:
            self.data[date_str] = {"entry": None, "exit": None, "notes": ""}
        self.data[date_str]["entry"] = entry_time
        self.save_data()
        return True
    
    def register_exit(self, date_str, exit_time, notes):
        """Registrar hora de salida"""
        if date_str not in self.data:
            self.data[date_str] = {"entry": None, "exit": None, "notes": ""}
        self.data[date_str]["exit"] = exit_time
        self.data[date_str]["notes"] = notes
        self.save_data()
        return True
    
    def calculate_hours(self, date_str):
        """Calcular horas trabajadas"""
        if (date_str in self.data and 
            self.data[date_str]["entry"] and 
            self.data[date_str]["exit"]):
            
            try:
                entry = datetime.datetime.strptime(self.data[date_str]["entry"], "%H:%M")
                exit = datetime.datetime.strptime(self.data[date_str]["exit"], "%H:%M")
                
                # Si la salida es antes que la entrada, asumimos que es del día siguiente
                if exit < entry:
                    exit = exit.replace(day=exit.day + 1)
                
                horas = (exit - entry).total_seconds() / 3600
                return round(horas, 2)
            except:
                return None
        return None
    
    def get_week_data(self, start_date):
        """Obtener datos de la semana"""
        week_data = {}
        total_horas = 0
        dias_trabajados = 0
        
        for i in range(7):
            current_date = start_date + datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            if date_str in self.data:
                horas = self.calculate_hours(date_str)
                if horas:
                    week_data[date_str] = {
                        "entry": self.data[date_str]["entry"],
                        "exit": self.data[date_str]["exit"],
                        "hours": horas,
                        "notes": self.data[date_str]["notes"]
                    }
                    total_horas += horas
                    dias_trabajados += 1
        
        return {
            "days": week_data,
            "total_hours": total_horas,
            "days_worked": dias_trabajados,
            "avg_per_day": total_horas / dias_trabajados if dias_trabajados > 0 else 0
        }

def main():
    st.title("⏰ Control de Horas de Trabajo")
    st.markdown("---")
    
    # Inicializar tracker
    tracker = TimeTracker()
    
    # Navegación
    menu = st.sidebar.selectbox(
        "Navegación",
        ["Registrar Horas", "Resumen Semanal", "Historial"]
    )
    
    today = datetime.date.today()
    
    if menu == "Registrar Horas":
        st.header("📝 Registrar Horas del Día")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fecha = st.date_input("Fecha", today)
            fecha_str = fecha.strftime("%Y-%m-%d")
            
            # Mostrar info existente
            if fecha_str in tracker.data:
                st.info("**Registro existente:**")
                if tracker.data[fecha_str]["entry"]:
                    st.write(f"✅ Entrada: {tracker.data[fecha_str]['entry']}")
                if tracker.data[fecha_str]["exit"]:
                    st.write(f"🚪 Salida: {tracker.data[fecha_str]['exit']}")
                if tracker.data[fecha_str]["notes"]:
                    st.write(f"📝 Notas: {tracker.data[fecha_str]['notes']}")
                
                horas = tracker.calculate_hours(fecha_str)
                if horas:
                    st.success(f"⏱️ Horas trabajadas: {horas} horas")
        
        with col2:
            st.subheader("Nuevo Registro")
            
            # Formulario simplificado
            hora_entrada = st.time_input("Hora de entrada", datetime.time(9, 0))
            hora_salida = st.time_input("Hora de salida", datetime.time(18, 0))
            notas = st.text_area("Notas del día", "")
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                if st.button("🟢 Registrar Entrada", use_container_width=True):
                    if tracker.register_entry(fecha_str, hora_entrada.strftime("%H:%M")):
                        st.success(f"Entrada registrada: {hora_entrada.strftime('%H:%M')}")
            
            with col_btn2:
                if st.button("🔴 Registrar Salida", use_container_width=True):
                    if tracker.register_exit(fecha_str, hora_salida.strftime("%H:%M"), notas):
                        st.success(f"Salida registrada: {hora_salida.strftime('%H:%M')}")
                        horas = tracker.calculate_hours(fecha_str)
                        if horas:
                            st.info(f"Horas trabajadas: {horas} horas")
    
    elif menu == "Resumen Semanal":
        st.header("📊 Resumen Semanal")
        
        # Selector de semana
        semana_actual = today - datetime.timedelta(days=today.weekday())
        semana_seleccionada = st.slider(
            "Selecciona la semana:",
            min_value=-4,
            max_value=4,
            value=0,
            format="Semana %d"
        )
        
        inicio_semana = semana_actual + datetime.timedelta(weeks=semana_seleccionada)
        datos_semana = tracker.get_week_data(inicio_semana)
        
        # Métricas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Horas", f"{datos_semana['total_hours']:.2f}h")
        with col2:
            st.metric("Días Trabajados", datos_semana['days_worked'])
        with col3:
            st.metric("Promedio por Día", f"{datos_semana['avg_per_day']:.2f}h")
        
        # Tabla de la semana
        st.subheader("Detalle de la Semana")
        dias_semana = []
        
        for i in range(7):
            dia = inicio_semana + datetime.timedelta(days=i)
            dia_str = dia.strftime("%Y-%m-%d")
            nombre_dia = dia.strftime("%A")
            fecha_formateada = dia.strftime("%d/%m/%Y")
            
            if dia_str in datos_semana['days']:
                datos_dia = datos_semana['days'][dia_str]
                dias_semana.append({
                    "Día": f"{nombre_dia} ({fecha_formateada})",
                    "Entrada": datos_dia['entry'],
                    "Salida": datos_dia['exit'],
                    "Horas": f"{datos_dia['hours']}h",
                    "Notas": datos_dia['notes'][:30] + "..." if len(datos_dia['notes']) > 30 else datos_dia['notes']
                })
            else:
                dias_semana.append({
                    "Día": f"{nombre_dia} ({fecha_formateada})",
                    "Entrada": "-",
                    "Salida": "-",
                    "Horas": "-",
                    "Notas": "-"
                })
        
        df_semana = pd.DataFrame(dias_semana)
        st.dataframe(df_semana, use_container_width=True)
    
    elif menu == "Historial":
        st.header("📋 Historial Completo")
        
        if not tracker.data:
            st.info("No hay registros aún. ¡Comienza registrando tus horas!")
            return
        
        # Convertir a DataFrame
        registros = []
        for fecha_str, datos in tracker.data.items():
            fecha_obj = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            horas = tracker.calculate_hours(fecha_str)
            
            registros.append({
                "Fecha": fecha_obj.strftime("%d/%m/%Y"),
                "Día": fecha_obj.strftime("%A"),
                "Entrada": datos.get("entry", "-"),
                "Salida": datos.get("exit", "-"),
                "Horas": f"{horas:.2f}h" if horas else "-",
                "Notas": datos.get("notes", "")
            })
        
        df = pd.DataFrame(registros)
        df = df.sort_values("Fecha", ascending=False)
        
        # Filtros simples
        st.subheader("Todos los Registros")
        st.dataframe(df, use_container_width=True)
        
        # Estadísticas
        total_horas = sum(float(hora.replace('h', '')) for hora in df['Horas'] if hora != '-')
        total_dias = len(df[df['Horas'] != '-'])
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Días", total_dias)
        with col2:
            st.metric("Total de Horas", f"{total_horas:.2f}h")

if __name__ == "__main__":
    main()
