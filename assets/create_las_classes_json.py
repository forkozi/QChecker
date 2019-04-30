import json


las_classes = {
  '1.4': {
    'classes': {
      '00': 'never classified',
      '01': 'Unclassified',
      '02': 'Ground',
      '03': 'Low Vegetation',
      '04': 'Medium Vegetation',
      '05': 'High Vegetation',
      '06': 'Building',
      '07': 'Low Point (noise)',
      '08': '*Reserved*',
      '09': 'Water',
      '10': 'Rail',
      '11': 'Road Surface',
      '12': '*Reserved*',
      '13': 'Wire -- Guard (Shield)',
      '14': 'Wire -- Conductor (Phase)',
      '15': 'Transmission Tower',
      '16': 'Wire-structure Connector (e.g Insulator)',
      '17': 'Bridge Deck',
      '18': 'High Noise',
      '19': '?',
      '20': '?',
      '21': '?',
      '22': '?',
    },
    'supplemental': {
      'Topo-Bathy Lidar Domain Profile': {
        'classes': {
          '40': 'Bathymetric point',
          '41': 'Water surface',
          '42': 'Derived water surface',
          '43': 'Submerged object',
          '44': 'IHO S-57 object',
          '45': 'No-bottom-found-at',
        },
        'Description': 'This domain profile adds point classification values for bathymetric lidar data.',
      },
    },
    'label': 'Las v1.4 (R14) Classifications'
  },
  '1.2': {
    'classes': {
      '00': 'never classified',
      '01': 'Unclassified',
      '02': 'Ground',
      '03': 'Low Vegetation',
      '04': 'Medium Vegetation',
      '05': 'High Vegetation',
      '06': 'Building',
      '07': 'Low Point (noise)',
      '08': '*Reserved*',
      '09': 'Water',
      '10': 'Rail',
      '11': 'Road Surface',
      '12': '*Reserved*',
      '13': 'Wire -- Guard (Shield)',
      '14': 'Wire -- Conductor (Phase)',
      '15': 'Transmission Tower',
      '16': 'Wire-structure Connector (e.g Insulator)',
      '17': 'Bridge Deck',
      '18': 'High Noise',
    },
    'supplemental': {
      'RSD Supplemental Classes': {
        'classes': {
          '23': 'Unrefracted Sensor Noise',
          '24': 'Refracted Sensor Noise',
          '25': 'Water Column',
          '26': 'Bathymetric Point',
          '27': 'Water Surface',
          '28': 'Derived Water Surface',
          '29': 'Submerged Object',
          '30': 'IHO S-57 Object',
        },
        'Description': r'These are non-standard supplemental classes defined by NOAA\'s Remote Sensing Division.',
      },
    },
    'label': 'Las v1.2 (R??) Classifications'
  }
}



with open('Z:\QChecker\QChecker_GITHUB\las_classes.json', 'w') as f:
    json.dump(las_classes, f)

