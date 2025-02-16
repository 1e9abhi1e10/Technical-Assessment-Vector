import { useState } from 'react';
import {
    Box,
    TextField,
    Button,
    Table,
    TableBody,
    TableCell,
    TableContainer,
    TableHead,
    TableRow,
    Paper,
} from '@mui/material';
import axios from 'axios';

const endpointMapping = {
    'Notion': 'notion',
    'Airtable': 'airtable',
    'HubSpot': 'hubspot',
};

export const DataForm = ({ integrationType, credentials }) => {
    const [loadedData, setLoadedData] = useState(null);
    const endpoint = endpointMapping[integrationType];

    // Load data from the selected integration
    const handleLoad = async () => {
        try {
            const formData = new FormData();
            formData.append('credentials', JSON.stringify(credentials));
            const response = await axios.post(`http://localhost:8000/integrations/${endpoint}/load`, formData);
            setLoadedData(response.data);
        } catch (e) {
            alert(e?.response?.data?.detail || e.message);
        }
    }

    // Render a single row in the data table
    const renderTableRow = (item) => (
        <TableRow key={item.id}>
            <TableCell>{item.id}</TableCell>
            <TableCell>{item.name}</TableCell>
            <TableCell>{item.email}</TableCell>
            <TableCell>{item.metadata?.company || 'N/A'}</TableCell>
            <TableCell>{item.metadata?.phone || 'N/A'}</TableCell>
        </TableRow>
    );

    // Render the data in either table or JSON format
    const renderData = () => {
        if (!loadedData) return null;
        
        if (Array.isArray(loadedData)) {
            return (
                <TableContainer component={Paper} sx={{mt: 2}}>
                    <Table>
                        <TableHead>
                            <TableRow>
                                <TableCell>ID</TableCell>
                                <TableCell>Name</TableCell>
                                <TableCell>Email</TableCell>
                                <TableCell>Company</TableCell>
                                <TableCell>Phone</TableCell>
                            </TableRow>
                        </TableHead>
                        <TableBody>
                            {loadedData.map((item) => renderTableRow(item))}
                        </TableBody>
                    </Table>
                </TableContainer>
            );
        }

        return (
            <TextField
                label="Loaded Data"
                value={JSON.stringify(loadedData, null, 2)}
                multiline
                sx={{mt: 2}}
                InputLabelProps={{ shrink: true }}
                disabled
            />
        );
    }

    return (
        <Box display='flex' justifyContent='center' alignItems='center' flexDirection='column' width='100%'>
            <Box display='flex' flexDirection='column' width='100%'>
                {renderData()}
                <Button
                    onClick={handleLoad}
                    sx={{mt: 2}}
                    variant='contained'
                >
                    Load Data
                </Button>
                <Button
                    onClick={() => setLoadedData(null)}
                    sx={{mt: 1}}
                    variant='contained'
                >
                    Clear Data
                </Button>
            </Box>
        </Box>
    );
}
