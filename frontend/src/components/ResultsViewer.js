import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Tabs,
  Tab,
  Grid,
  Card,
  CardMedia,
  CardContent,
  Button,
} from '@mui/material';
import ReactMarkdown from 'react-markdown';
import AssessmentIcon from '@mui/icons-material/Assessment';
import ImageIcon from '@mui/icons-material/Image';
import DataObjectIcon from '@mui/icons-material/DataObject';
import DownloadIcon from '@mui/icons-material/Download';
import AutoGraphIcon from '@mui/icons-material/AutoGraph';

function TabPanel({ children, value, index }) {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 4 }}>{children}</Box>}
    </div>
  );
}

function ResultsViewer({ result }) {
  const [tabValue, setTabValue] = useState(0);
  const [reportContent, setReportContent] = useState('');
  const [deepReportContent, setDeepReportContent] = useState('');
  const [visualizations, setVisualizations] = useState([]);

  useEffect(() => {
    // Fetch report content
    if (result.report_path) {
      fetchFileContent(result.report_path).then(setReportContent);
    }

    // Fetch deep report if available
    if (result.deep_report_path) {
      fetchFileContent(result.deep_report_path).then(setDeepReportContent);
    }

    // Fetch visualizations
    fetchVisualizations();
  }, [result]);

  const fetchFileContent = async (path) => {
    try {
      const response = await fetch(`/api/file/${path}`);
      const data = await response.json();
      return data.content || '';
    } catch (error) {
      console.error('Error fetching file:', error);
      return 'Error loading content';
    }
  };

  const fetchVisualizations = async () => {
    try {
      const response = await fetch('/api/outputs');
      const data = await response.json();
      const viz = data.visualizations || [];
      // Deduplicate by path
      const unique = Array.from(new Map(viz.map(v => [v.path, v])).values());
      setVisualizations(unique);
    } catch (error) {
      console.error('Error fetching visualizations:', error);
    }
  };

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  return (
    <Paper
      elevation={0}
      className="glass-panel"
      sx={{
        borderRadius: 4,
        overflow: 'hidden',
        minHeight: '600px',
        display: 'flex',
        flexDirection: 'column'
      }}
    >
      <Box sx={{ borderBottom: '1px solid rgba(255,255,255,0.08)', bgcolor: 'rgba(0,0,0,0.2)' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            px: 2,
            '& .MuiTab-root': {
              color: 'rgba(255,255,255,0.6)',
              fontWeight: 600,
              textTransform: 'none',
              fontSize: '0.95rem',
              minHeight: 64
            },
            '& .Mui-selected': {
              color: '#e10600 !important',
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#e10600',
              height: 3
            },
          }}
        >
          <Tab icon={<AssessmentIcon />} iconPosition="start" label="Analysis Report" />
          {deepReportContent && <Tab icon={<AutoGraphIcon />} iconPosition="start" label="Deep Strategy Analysis" />}
          <Tab icon={<ImageIcon />} iconPosition="start" label={`Telemetry & Visuals (${visualizations.length})`} />
          <Tab icon={<DataObjectIcon />} iconPosition="start" label="Data & Metrics" />
        </Tabs>
      </Box>

      <Box sx={{ flexGrow: 1, bgcolor: 'rgba(0,0,0,0.1)' }}>
        <TabPanel value={tabValue} index={0}>
          <Box
            sx={{
              color: 'rgba(255,255,255,0.9)',
              '& h1': { color: '#e10600', mt: 2, mb: 2, fontSize: '2rem', fontFamily: 'Formula1' },
              '& h2': { color: 'white', mt: 4, mb: 2, borderBottom: '1px solid rgba(255,255,255,0.1)', pb: 1 },
              '& h3': { color: '#00d2be', mt: 3, mb: 1.5 },
              '& p': { mb: 2, lineHeight: 1.8, fontSize: '1.05rem' },
              '& ul, & ol': { pl: 3, mb: 2 },
              '& li': { mb: 1 },
              '& strong': { color: 'white', fontWeight: 700 },
              '& code': {
                background: 'rgba(225, 6, 0, 0.1)',
                color: '#ff4d4d',
                padding: '2px 6px',
                borderRadius: '4px',
                fontFamily: 'monospace',
                fontSize: '0.9em'
              },
              '& pre': {
                background: '#0d1117',
                padding: '16px',
                borderRadius: '8px',
                overflow: 'auto',
                border: '1px solid rgba(255,255,255,0.05)'
              },
            }}
          >
            <ReactMarkdown>{reportContent}</ReactMarkdown>
          </Box>
        </TabPanel>

        {deepReportContent && (
          <TabPanel value={tabValue} index={1}>
            <Box
              sx={{
                color: 'rgba(255,255,255,0.9)',
                '& h1': { color: '#e10600', mt: 2, mb: 2, fontSize: '2rem', fontFamily: 'Formula1' },
                '& h2': { color: 'white', mt: 4, mb: 2, borderBottom: '1px solid rgba(255,255,255,0.1)', pb: 1 },
                '& h3': { color: '#00d2be', mt: 3, mb: 1.5 },
                '& p': { mb: 2, lineHeight: 1.8, fontSize: '1.05rem' },
                '& ul, & ol': { pl: 3, mb: 2 },
                '& li': { mb: 1 },
                '& strong': { color: 'white', fontWeight: 700 },
                '& blockquote': {
                  borderLeft: '4px solid #e10600',
                  pl: 2,
                  py: 1,
                  my: 3,
                  bgcolor: 'rgba(225,6,0,0.05)',
                  fontStyle: 'italic'
                }
              }}
            >
              <ReactMarkdown>{deepReportContent}</ReactMarkdown>
            </Box>
          </TabPanel>
        )}

        <TabPanel value={tabValue} index={deepReportContent ? 2 : 1}>
          <Grid container spacing={3}>
            {visualizations.length === 0 && (
              <Grid item xs={12}>
                <Box
                  sx={{
                    p: 4,
                    textAlign: 'center',
                    background: 'rgba(255,255,255,0.02)',
                    border: '1px dashed rgba(255,255,255,0.1)',
                    borderRadius: 2,
                    color: 'rgba(255,255,255,0.5)',
                  }}
                >
                  <Typography variant="h6">No visualizations generated yet.</Typography>
                  <Typography variant="body2">Charts and telemetry will appear here once the relevant analysis step completes.</Typography>
                </Box>
              </Grid>
            )}
            {visualizations.map((viz, index) => {
              const imgUrl = `/api/file/${viz.path}`;
              return (
                <Grid item xs={12} md={6} key={index}>
                  <Card
                    sx={{
                      background: 'rgba(22, 27, 34, 0.9)',
                      color: 'white',
                      border: '1px solid rgba(255,255,255,0.08)',
                      borderRadius: 3,
                      overflow: 'hidden',
                      transition: 'transform 0.2s',
                      //   '&:hover': { transform: 'scale(1.02)' }
                    }}
                  >
                    <CardMedia
                      component="img"
                      image={imgUrl}
                      alt={viz.name}
                      sx={{
                        height: 300,
                        objectFit: 'contain',
                        p: 2,
                        bgcolor: 'white' // Make charts readable against white as they likely have transparent/white bg
                      }}
                    />
                    <CardContent sx={{ borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                      <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 600 }}>
                        {viz.name.replace('.png', '').replace(/_/g, ' ').toUpperCase()}
                      </Typography>
                      <Button
                        size="small"
                        startIcon={<DownloadIcon />}
                        href={imgUrl}
                        download
                        variant="outlined"
                        sx={{
                          mt: 1,
                          borderColor: 'rgba(255,255,255,0.2)',
                          color: 'white',
                          '&:hover': {
                            borderColor: '#e10600',
                            color: '#e10600',
                            bgcolor: 'rgba(225,6,0,0.05)'
                          }
                        }}
                      >
                        Download Chart
                      </Button>
                    </CardContent>
                  </Card>
                </Grid>
              );
            })}
          </Grid>
        </TabPanel>

        <TabPanel value={tabValue} index={deepReportContent ? 3 : 2}>
          <Box sx={{ color: 'white' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#00d2be' }}>
              LLM Usage Metrics
            </Typography>
            {result.token_usage && (
              <Grid container spacing={2} sx={{ mb: 4 }}>
                <Grid item xs={4}>
                  <Box sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.03)', borderRadius: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Prompt</Typography>
                    <Typography variant="h5" fontWeight="bold">{result.token_usage.prompt_tokens}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ p: 2, bgcolor: 'rgba(255,255,255,0.03)', borderRadius: 2, textAlign: 'center' }}>
                    <Typography variant="body2" color="text.secondary">Completion</Typography>
                    <Typography variant="h5" fontWeight="bold">{result.token_usage.completion_tokens}</Typography>
                  </Box>
                </Grid>
                <Grid item xs={4}>
                  <Box sx={{ p: 2, bgcolor: 'rgba(225,6,0,0.1)', borderRadius: 2, textAlign: 'center', border: '1px solid rgba(225,6,0,0.3)' }}>
                    <Typography variant="body2" sx={{ color: '#ff4d4d' }}>Total</Typography>
                    <Typography variant="h5" fontWeight="bold" sx={{ color: 'white' }}>{result.token_usage.total_tokens}</Typography>
                  </Box>
                </Grid>
              </Grid>
            )}

            <Typography variant="h6" gutterBottom sx={{ mt: 3, color: '#00d2be' }}>
              Generated Artifacts
            </Typography>
            <Box sx={{ p: 2, background: 'rgba(0,0,0,0.2)', borderRadius: 2, fontFamily: 'monospace', fontSize: '0.85rem' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <span>📄</span>
                <span style={{ color: 'rgba(255,255,255,0.7)' }}>{result.report_path}</span>
              </Box>
              {result.deep_report_path && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <span>📄</span>
                  <span style={{ color: 'rgba(255,255,255,0.7)' }}>{result.deep_report_path}</span>
                </Box>
              )}
              {visualizations.map((viz, idx) => (
                <Box key={idx} sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <span>🖼️</span>
                  <span style={{ color: 'rgba(255,255,255,0.7)' }}>{viz.path}</span>
                </Box>
              ))}
            </Box>
          </Box>
        </TabPanel>
      </Box>
    </Paper>
  );
}

export default ResultsViewer;
