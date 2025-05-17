# app/routes.py
import bcrypt
from flask import Blueprint, render_template, request, redirect, url_for, session
from flask import Flask, render_template, request, redirect, url_for, session, flash
from .db import get_db_connection

routes_blueprint = Blueprint('routes', __name__)

## Creación de Login
@routes_blueprint.route('/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        correo = request.form['username']
        contrasena = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuarios WHERE correo_electronico = %s", (correo,))
            usuario = cursor.fetchone()
            conn.close()

            if usuario:
                if usuario['estado'].lower() == 'inactivo':
                    error = '⚠️ Usuario inactivo. Contacte con el administrador.'
                elif bcrypt.checkpw(contrasena.encode('utf-8'), usuario['contrasena'].encode('utf-8')):
                    session['usuario'] = usuario['nombre_completo']
                    session['rol'] = usuario['rol']
                    return redirect(url_for('routes.dashboard'))
                else:
                    error = '⚠️ Contraseña incorrecta.'
            else:
                error = '⚠️ Usuario no encontrado.'

        except Exception as e:
            error = f'❌ Error de base de datos: {e}'

    return render_template('login.html', error=error)

@routes_blueprint.route('/dashboard')
def dashboard():
    if 'usuario' in session:
        return render_template('dashboard.html', usuario=session['usuario'], rol=session['rol'])
    else:
        return redirect(url_for('routes.login'))


@routes_blueprint.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('routes.login'))


## Creación de formulario para ABM
@routes_blueprint.route('/crear_usuario', methods=['GET', 'POST'])
def crear_usuario():
    if 'rol' not in session or session['rol'] != 'Administrador':
        return redirect(url_for('routes.dashboard'))

    mensaje = None
    error = None

    if request.method == 'POST':
        nombre = request.form['nombre_completo']
        correo = request.form['correo_electronico']
        contrasena = request.form['contrasena']
        rol = request.form['rol']
        estado = request.form['estado']

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            hashed_password = bcrypt.hashpw(contrasena.encode('utf-8'), bcrypt.gensalt())
            cursor.execute("""
                INSERT INTO usuarios (nombre_completo, correo_electronico, contrasena, rol, estado)
                VALUES (%s, %s, %s, %s, %s)
            """, (nombre, correo, hashed_password.decode('utf-8'), rol, estado))
            conn.commit()
            conn.close()
            mensaje = "✅ Usuario creado exitosamente."
        except Exception as e:
            error = f"❌ Error al crear usuario: {e}"

    return render_template('crear_usuario.html', mensaje=mensaje, error=error)

##Listar usuarios
@routes_blueprint.route('/usuarios', methods=['GET'])
def listar_usuarios():
    if 'rol' not in session or session['rol'] != 'Administrador':
        return redirect(url_for('routes.login'))

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, nombre_completo, correo_electronico, rol, estado FROM usuarios")
        usuarios = cursor.fetchall()
        conn.close()
    except Exception as e:
        usuarios = []
        flash(f"Error al obtener los usuarios: {e}", "danger")

    return render_template('usuarios.html', usuarios=usuarios)

##Cambiar estodos desactivar/activar
@routes_blueprint.route('/cambiar_estado/<int:id>', methods=['POST'])
def cambiar_estado(id):
    if 'rol' not in session or session['rol'] != 'Administrador':
        return redirect(url_for('routes.login'))

    nuevo_estado = request.form.get('estado')
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE usuarios SET estado = %s WHERE id = %s", (nuevo_estado, id))
        conn.commit()
        conn.close()
        flash("✅ Estado actualizado correctamente", "success")
    except Exception as e:
        flash(f"❌ Error al actualizar el estado: {e}", "danger")

    return redirect(url_for('routes.listar_usuarios'))
