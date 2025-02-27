-- Tabla de Agentes (incluye Monitores)
CREATE TABLE agentes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    nip VARCHAR(6) NOT NULL UNIQUE,
    seccion TEXT NOT NULL CHECK (seccion IN ('Motorista', 'Patrullas', 'GOA', 'Atestados')),
    grupo TEXT NOT NULL CHECK (grupo IN ('G-1', 'G-2', 'G-3')),
    email TEXT UNIQUE,
    telefono TEXT,
    es_monitor BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de Actividades
CREATE TABLE actividades (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL UNIQUE,
    descripcion TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabla de Turnos
CREATE TABLE turnos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nombre TEXT NOT NULL UNIQUE CHECK (nombre IN ('Mañana', 'Tarde', 'Noche')),
    hora_inicio TIME,
    hora_fin TIME,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insertar actividades iniciales
INSERT INTO actividades (nombre, descripcion) VALUES 
('Defensa Personal', 'Curso de técnicas de defensa personal'),
('Acondicionamiento Físico', 'Entrenamiento físico general');

-- Insertar turnos
INSERT INTO turnos (nombre, hora_inicio, hora_fin) VALUES 
('Mañana', '08:00:00', '14:00:00'),
('Tarde', '14:00:00', '22:00:00'),
('Noche', '22:00:00', '08:00:00');

