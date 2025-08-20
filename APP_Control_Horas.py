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
    
    def register_time(self, date_str, time_type, time_value, notes=""):
        """Registrar hora (entrada o salida)"""
        if date_str not in self.data:
            self.data[date_str] = {"entry": None, "exit": None, "notes": ""}
        
        self.data[date_str][time_type] = time_value
        if notes:
            self.data[date_str]["notes"] = notes
        
        self.save_data()
        return True
    
    def delete_record(self, date_str):
        """Eliminar registro de un día"""
        if date_str in self.data:
            del self.data[date_str]
            self.save_data()
            return True
        return False
    
    def calculate_hours(self, date_str, apply_break=True):
        """Calcular horas trabajadas con descuento de 30 minutos"""
        if (date_str in self.data and 
            self.data[date_str]["entry"] and 
            self.data[date_str]["exit"]):
            
            try:
                entry = datetime.datetime.strptime(self.data[date_str]["entry"], "%H:%M")
                exit = datetime.datetime.strptime(self.data[date_str]["exit"], "%H:%M")
                
                # Si la salida es antes que la entrada, asumimos que es del día siguiente
                if exit < entry:
                    exit = exit.replace(day=exit.day + 1)
                
                horas_brutas = (exit - entry).total_seconds() / 3600
                
                # Aplicar descuento de 30 minutos si se trabaja más de 5 horas
                if apply_break and horas_brutas > 5:
                    horas_netas = horas_brutas - 0.5  # 30 minutos de descanso
                else:
                    horas_netas = horas_brutas
                
                return round(horas_netas, 2), round(horas_brutas, 2)
            except:
                return None, None
        return None, None
    
    def get_week_data(self, start_date):
        """Obtener datos de la semana"""
        week_data = {}
        total_horas_netas = 0
        total_horas_brutas = 0
        dias_trabajados = 0
        
        for i in range(7):
            current_date = start_date + datetime.timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            if date_str in self.data:
                horas_netas, horas_brutas = self.calculate_hours(date_str)
                if horas_netas:
                    week_data[date_str] = {
                        "entry": self.data[date_str]["entry"],
                        "exit": self.data[date_str]["exit"],
                        "hours_net": horas_netas,
                        "hours_gross": horas_brutas,
                        "notes": self.data[date_str]["notes"],
                        "has_break": horas_brutas > 5  # Indica si aplicó descanso
                    }
                    total_horas_netas += horas_netas
                    total_horas_brutas += horas_brutas
                    dias_trabajados += 1
        
        return {
            "days": week_data,
            "total_hours_net": total_horas_netas,
            "total_hours_gross": total_horas_brutas,
            "days_worked": dias_trabajados,
            "avg_per_day": total_horas_netas / dias_trabajados if dias_trabajados > 0 else 0
        }

def main():
    st.title("⏰ Control de Horas de Trabajo")
    st.markdown("---")
    
    # Inicializar tracker
    tracker = TimeTracker()
    
    # Navegación
    menu = st.sidebar.selectbox(
        "Navegación",
        ["Registrar Horas", "Resumen Semanal", "Historial", "Administrar Registros"]
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
                
                horas_netas, horas_brutas = tracker.calculate_hours(fecha_str)
                if horas_netas:
                    st.success(f"⏱️ Horas netas: {horas_netas} horas (brutas: {horas_brutas}h)")
                    if horas_brutas > 5:
                        st.info("ℹ️ Se aplicó descuento de 30 minutos por descanso")
        
        with col2:
            st.subheader("Nuevo Registro")
            
            # Selector de tipo de registro
            registro_tipo = st.radio(
                "Tipo de registro:",
                ["Entrada", "Salida"],
                horizontal=True,
                help="Selecciona si vas a registrar la entrada o la salida"
            )
            
            # Hora actual por defecto
            ahora = datetime.datetime.now().time()
            hora_registro = st.time_input(
                f"Hora de {registro_tipo.lower()}:",
                value=ahora
            )
            
            notas = st.text_area("Notas del día", "")
            
            if st.button(f"📝 Registrar {registro_tipo}", type="primary", use_container_width=True):
                time_type = "entry" if registro_tipo == "Entrada" else "exit"
                
                if tracker.register_time(fecha_str, time_type, hora_registro.strftime("%H:%M"), notas):
                    st.success(f"✅ {registro_tipo} registrada: {hora_registro.strftime('%H:%M')}")
                    
                    # Si se registró salida, calcular horas
                    if registro_tipo == "Salida" and tracker.data[fecha_str]["entry"]:
                        horas_netas, horas_brutas = tracker.calculate_hours(fecha_str)
                        if horas_netas:
                            st.info(f"⏱️ Horas trabajadas: {horas_netas} horas netas")
                            if horas_brutas > 5:
                                st.info("ℹ️ Se descontaron 30 minutos por descanso")
    
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
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Horas Netas", f"{datos_semana['total_hours_net']:.2f}h")
        with col2:
            st.metric("Total Horas Brutas", f"{datos_semana['total_hours_gross']:.2f}h")
        with col3:
            st.metric("Días Trabajados", datos_semana['days_worked'])
        with col4:
            st.metric("Promedio por Día", f"{datos_semana['avg_per_day']:.2f}h")
        
        # Descuento total por descansos
        descuento_total = datos_semana['total_hours_gross'] - datos_semana['total_hours_net']
        st.info(f"💰 Total descontado por descansos: {descuento_total:.2f} horas")
        
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
                descanso_info = "✓" if datos_dia['has_break'] else "✗"
                
                dias_semana.append({
                    "Día": f"{nombre_dia} ({fecha_formateada})",
                    "Entrada": datos_dia['entry'],
                    "Salida": datos_dia['exit'],
                    "Horas Brutas": f"{datos_dia['hours_gross']}h",
                    "Horas Netas": f"{datos_dia['hours_net']}h",
                    "Descanso": descanso_info,
                    "Notas": datos_dia['notes'][:30] + "..." if len(datos_dia['notes']) > 30 else datos_dia['notes']
                })
            else:
                dias_semana.append({
                    "Día": f"{nombre_dia} ({fecha_formateada})",
                    "Entrada": "-",
                    "Salida": "-",
                    "Horas Brutas": "-",
                    "Horas Netas": "-",
                    "Descanso": "-",
                    "Notas": "-"
                })
        
        df_semana = pd.DataFrame(dias_semana)
        st.dataframe(df_semana, use_container_width=True)
        
        # Gráfico de horas
        if datos_semana['days_worked'] > 0:
            st.subheader("📈 Distribución de Horas")
            
            chart_data = []
            for dia_str, datos in datos_semana['days'].items():
                dia_fecha = datetime.datetime.strptime(dia_str, "%Y-%m-%d")
                chart_data.append({
                    "Día": dia_fecha.strftime("%a %d/%m"),
                    "Horas Netas": datos['hours_net'],
                    "Horas Brutas": datos['hours_gross']
                })
            
            if chart_data:
                chart_df = pd.DataFrame(chart_data)
                st.bar_chart(chart_df.set_index("Día"))
    
    elif menu == "Historial":
        st.header("📋 Historial Completo")
        
        if not tracker.data:
            st.info("No hay registros aún. ¡Comienza registrando tus horas!")
            return
        
        # Convertir a DataFrame
        registros = []
        for fecha_str, datos in tracker.data.items():
            fecha_obj = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            horas_netas, horas_brutas = tracker.calculate_hours(fecha_str)
            
            registros.append({
                "Fecha": fecha_obj.strftime("%d/%m/%Y"),
                "Día": fecha_obj.strftime("%A"),
                "Entrada": datos.get("entry", "-"),
                "Salida": datos.get("exit", "-"),
                "Horas Brutas": f"{horas_brutas:.2f}h" if horas_brutas else "-",
                "Horas Netas": f"{horas_netas:.2f}h" if horas_netas else "-",
                "Notas": datos.get("notes", "")
            })
        
        df = pd.DataFrame(registros)
        df = df.sort_values("Fecha", ascending=False)
        
        # Filtros
        st.subheader("Todos los Registros")
        st.dataframe(df, use_container_width=True)
        
        # Estadísticas
        total_horas_netas = sum(float(hora.replace('h', '')) for hora in df['Horas Netas'] if hora != '-')
        total_horas_brutas = sum(float(hora.replace('h', '')) for hora in df['Horas Brutas'] if hora != '-')
        total_dias = len(df[df['Horas Netas'] != '-'])
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Días", total_dias)
        with col2:
            st.metric("Total Horas Netas", f"{total_horas_netas:.2f}h")
        with col3:
            st.metric("Total Horas Brutas", f"{total_horas_brutas:.2f}h")
        
        st.info(f"💰 Total descontado por descansos: {total_horas_brutas - total_horas_netas:.2f} horas")
    
    elif menu == "Administrar Registros":
        st.header("🗑️ Administrar Registros")
        
        if not tracker.data:
            st.info("No hay registros para administrar")
            return
        
        # Lista de registros para eliminar
        st.subheader("Seleccionar registro para eliminar")
        
        registros_lista = []
        for fecha_str in sorted(tracker.data.keys(), reverse=True):
            fecha_obj = datetime.datetime.strptime(fecha_str, "%Y-%m-%d")
            registros_lista.append(fecha_obj.strftime("%Y-%m-%d (%d/%m/%Y)"))
        
        registro_seleccionado = st.selectbox(
            "Selecciona el registro a eliminar:",
            registros_lista
        )
        
        # Extraer la fecha del formato seleccionado
        if registro_seleccionado:
            fecha_eliminar = registro_seleccionado.split(" ")[0]
            
            # Mostrar detalles del registro seleccionado
            if fecha_eliminar in tracker.data:
                datos = tracker.data[fecha_eliminar]
                st.warning("**Registro seleccionado:**")
                st.write(f"📅 Fecha: {fecha_eliminar}")
                st.write(f"🟢 Entrada: {datos.get('entry', 'No registrada')}")
                st.write(f"🔴 Salida: {datos.get('exit', 'No registrada')}")
                st.write(f"📝 Notas: {datos.get('notes', 'Sin notas')}")
                
                horas_netas, horas_brutas = tracker.calculate_hours(fecha_eliminar)
                if horas_netas:
                    st.write(f"⏱️ Horas: {horas_netas}h netas ({horas_brutas}h brutas)")
                
                # Confirmación de eliminación
                if st.button("🗑️ Eliminar Registro", type="secondary"):
                    if tracker.delete_record(fecha_eliminar):
                        st.success("✅ Registro eliminado correctamente")
                        st.rerun()
                    else:
                        st.error("❌ Error al eliminar el registro")

if __name__ == "__main__":
    main()
