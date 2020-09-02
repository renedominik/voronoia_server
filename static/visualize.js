

function visualize(stage, download_url, lic_selection) {           
    // load molecule structure
    loadPDB(stage, download_url + "protein.pdb", "structure", ["cartoon", "licorice"],  [{colorScheme: 'bfactor'}, {sele: lic_selection}], true);

    // load cavaties
    loadPDB(stage, download_url + "onlyHoles.pdb", "holes", ["ball+stick"], [{radius: 'bfactor', colorscheme: 'bfactor'}]);
}


function loadPDB(stage, filename, name, representations, representation_dicts, center) {
    stage.loadFile(file, { defaultRepresentation: true }).then( function(comp) {
        comp.setName(name);
        comp.setSelection("");

        for(var i = 0; i < representations.length; i++) {
            comp.addRepresentation(representations[i], representation_dicts[i]);
        }

        if(center) {
            comp.centerView();
        }
    });
}
