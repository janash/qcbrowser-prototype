"""
Helper functions
"""

from openff.toolkit import Molecule

def gather_molecular_data(entry, 
                            store_entry=False, 
                            get_openff=True, 
                            get_rdkit=False,
                            include_error=False
                            ):
        """
        Helper function to gather molecular data from an entry.
        
        Parameters
        ----------
        entry : QCPortal Entry
            Entry object to process
        store_entry : bool, default=False
            If True, include original entry in output
        get_qcmol : bool, default=True
            If True, include OpenFF molecule
        get_rdkit_mol : bool, default=False
            If True, include RDKit molecules
            
        Returns
        -------
        dict
            Dictionary containing processed molecular data
        """
        data = {}
        
        if store_entry:
            data['Entry'] = entry
            
        if get_openff:
            try:
                data['OpenFFMol'] = Molecule.from_qcschema(entry)
            except Exception as e:
                data['OpenFFMol'] = None
                if include_error:
                    data['OpenFFMol_Error'] = str(e)
                
        if get_rdkit:
            try:
                if 'OpenFFMol' in data:
                    mol = data['OpenFFMol']
                else:
                    mol = Molecule.from_qcschema(entry)
                data['RDKit Molecule'] = mol.to_rdkit()
            except Exception as e:
                data['RDKit Molecule'] = None
                if include_error:
                    data['RDKit_Error'] = str(e)
                
        return data