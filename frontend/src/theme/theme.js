import { createTheme } from '@mui/material';

export const theme = createTheme({
    palette: {
        mode: 'dark',
        primary: {
            main: '#e10600', // Ferrari Red
            light: '#ff4d4d',
            dark: '#a80000',
        },
        secondary: {
            main: '#00d2be', // Mercedes Turquoise
            light: '#5fffe6',
            dark: '#00a08e',
        },
        background: {
            default: '#0b0c10',
            paper: '#1f2833',
        },
        text: {
            primary: '#ffffff',
            secondary: '#c5c6c7',
        },
        success: {
            main: '#00d2be',
        },
        info: {
            main: '#3498db',
        },
        warning: {
            main: '#f1c40f',
        },
        error: {
            main: '#e10600',
        },
    },
    typography: {
        fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
        h1: { fontFamily: '"Formula1", sans-serif', fontWeight: 700 },
        h2: { fontFamily: '"Formula1", sans-serif', fontWeight: 700 },
        h3: { fontFamily: '"Formula1", sans-serif', fontWeight: 700 },
        h4: { fontFamily: '"Formula1", sans-serif', fontWeight: 700 },
        h5: { fontFamily: '"Formula1", sans-serif', fontWeight: 700 },
        h6: { fontFamily: '"Formula1", sans-serif', fontWeight: 700, letterSpacing: '0.05em' },
        button: { fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.1em' },
    },
    components: {
        MuiCssBaseline: {
            styleOverrides: {
                body: {
                    scrollbarColor: "#e10600 #0b0c10",
                    "&::-webkit-scrollbar, & *::-webkit-scrollbar": {
                        width: "8px",
                        height: "8px",
                    },
                    "&::-webkit-scrollbar-thumb, & *::-webkit-scrollbar-thumb": {
                        borderRadius: 8,
                        backgroundColor: "#e10600",
                        minHeight: 24,
                    },
                    "&::-webkit-scrollbar-track, & *::-webkit-scrollbar-track": {
                        backgroundColor: "#0b0c10",
                    },
                },
            },
        },
        MuiPaper: {
            styleOverrides: {
                root: {
                    backgroundImage: 'none',
                    backgroundColor: 'rgba(31, 40, 51, 0.6)', // Glassmorphism base
                    backdropFilter: 'blur(12px)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    boxShadow: '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
                },
            },
        },
        MuiButton: {
            styleOverrides: {
                root: {
                    borderRadius: '4px', // F1 style is often sharp or slightly rounded
                    boxShadow: 'none',
                    '&:hover': {
                        boxShadow: '0 0 10px rgba(225, 6, 0, 0.5)',
                    },
                },
                containedPrimary: {
                    background: 'linear-gradient(45deg, #e10600 30%, #ff4500 90%)',
                },
            },
        },
        MuiChip: {
            styleOverrides: {
                root: {
                    borderRadius: '4px',
                    fontWeight: 600,
                },
            },
        },
    },
    shape: {
        borderRadius: 8,
    },
});
