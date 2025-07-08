class LocationLoader {
    constructor() {
        this.countries = [];
        this.phoneCodes = {
            // Fallback phone codes mapping
            'US': '+1', 'CA': '+1', 'TN': '+216', 'FR': '+33', 'GB': '+44',
            'DE': '+49', 'IT': '+39', 'ES': '+34', 'AU': '+61', 'JP': '+81',
            'CN': '+86', 'IN': '+91', 'BR': '+55', 'MX': '+52', 'RU': '+7',
            'EG': '+20', 'SA': '+966', 'AE': '+971', 'MA': '+212', 'DZ': '+213'
        };
        this.init();
    }

    async init() {
        console.log('LocationLoader initializing...');
        await this.loadCountries();
        this.setupEventListeners();
    }

    async loadCountries() {
        console.log('Attempting to load countries...');
        try {
            const response = await fetch('/api/countries');
            console.log('Response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('Countries data received:', data);
            
            this.countries = data;
            this.populateCountrySelect();
            this.populatePhoneSelect(); // Separate method for phone codes
        } catch (error) {
            console.error('Error loading countries:', error);
            console.log('Using fallback countries...');
            // Enhanced fallback with more countries
            this.countries = [
                { iso2: 'TN', name: 'Tunisia', phonecode: '+216' },
                { iso2: 'CA', name: 'Canada', phonecode: '+1' },
                { iso2: 'US', name: 'United States', phonecode: '+1' },
                { iso2: 'FR', name: 'France', phonecode: '+33' },
                { iso2: 'GB', name: 'United Kingdom', phonecode: '+44' },
                { iso2: 'DE', name: 'Germany', phonecode: '+49' },
                { iso2: 'IT', name: 'Italy', phonecode: '+39' },
                { iso2: 'ES', name: 'Spain', phonecode: '+34' },
                { iso2: 'MA', name: 'Morocco', phonecode: '+212' },
                { iso2: 'DZ', name: 'Algeria', phonecode: '+213' },
                { iso2: 'EG', name: 'Egypt', phonecode: '+20' }
            ];
            this.populateCountrySelect();
            this.populatePhoneSelect();
        }
    }

    populateCountrySelect() {
        console.log('Populating country select...');
        const countrySelect = document.getElementById('country');
        
        if (!countrySelect) {
            console.error('Country select element not found!');
            return;
        }

        // Clear existing options
        countrySelect.innerHTML = '<option value="">Select Country</option>';

        this.countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country.name;
            option.textContent = country.name;
            option.dataset.iso = country.iso2;
            // Store phone code in dataset
            option.dataset.phonecode = country.phonecode || this.phoneCodes[country.iso2] || '';
            countrySelect.appendChild(option);
        });
        
        console.log(`Populated ${this.countries.length} countries`);
    }

    populatePhoneSelect() {
        const phoneSelect = document.getElementById('phone_prefix');
        if (!phoneSelect) {
            console.log('Phone select element not found');
            return;
        }

        // Clear existing options
        phoneSelect.innerHTML = '<option value="">Select Phone Code</option>';

        // Create a unique list of phone codes
        const uniquePhoneCodes = new Map();
        
        this.countries.forEach(country => {
            const phoneCode = country.phonecode || this.phoneCodes[country.iso2];
            if (phoneCode && !uniquePhoneCodes.has(phoneCode)) {
                uniquePhoneCodes.set(phoneCode, country.name);
            }
        });

        // Add phone code options
        uniquePhoneCodes.forEach((countryName, phoneCode) => {
            const phoneOption = document.createElement('option');
            phoneOption.value = phoneCode;
            phoneOption.textContent = `${phoneCode}`;
            phoneSelect.appendChild(phoneOption);
        });

        console.log(`Populated ${uniquePhoneCodes.size} phone codes`);
    }

    async loadStates(countryIso) {
        console.log(`Loading states for country: ${countryIso}`);
        try {
            const response = await fetch(`/api/states/${countryIso}`);
            console.log('States response status:', response.status);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const states = await response.json();
            console.log('States data received:', states);
            this.populateStateSelect(states);
        } catch (error) {
            console.error('Error loading states:', error);
            this.populateStateSelect([]);
        }
    }

    populateStateSelect(states) {
        const stateSelect = document.getElementById('province');
        if (!stateSelect) {
            console.error('Province select element not found!');
            return;
        }

        stateSelect.innerHTML = '<option value="">Select State/Province</option>';
         
        if (states && states.length > 0) {
            states.forEach(state => {
                const option = document.createElement('option');
                option.value = state.name;
                option.textContent = state.name;
                option.dataset.iso = state.iso2;
                stateSelect.appendChild(option);
            });
            console.log(`Populated ${states.length} states/provinces`);
        } else {
            // If no states available, allow free text input
            const option = document.createElement('option');
            option.value = 'other';
            option.textContent = 'Other (type manually)';
            stateSelect.appendChild(option);
            console.log('No states found, added manual input option');
        }
    }

    setupEventListeners() {
        const countrySelect = document.getElementById('country');
        const phoneSelect = document.getElementById('phone_prefix');
        
        if (countrySelect) {
            countrySelect.addEventListener('change', (e) => {
                const selectedOption = e.target.options[e.target.selectedIndex];
                const countryIso = selectedOption.dataset.iso;
                const phoneCode = selectedOption.dataset.phonecode;
                
                console.log(`Country changed to: ${e.target.value} (${countryIso})`);
                
                if (countryIso) {
                    this.loadStates(countryIso);
                    
                    // Auto-select phone code if available
                    if (phoneSelect && phoneCode) {
                        phoneSelect.value = phoneCode;
                        console.log(`Auto-selected phone code: ${phoneCode}`);
                    }
                } else {
                    // Clear states if no country selected
                    this.populateStateSelect([]);
                }
            });
        }

        // Handle manual state input if "Other" is selected
        const stateSelect = document.getElementById('province');
        if (stateSelect) {
            stateSelect.addEventListener('change', (e) => {
                if (e.target.value === 'other') {
                    const manualInput = prompt('Please enter your state/province:');
                    if (manualInput && manualInput.trim()) {
                        const option = document.createElement('option');
                        option.value = manualInput.trim();
                        option.textContent = manualInput.trim();
                        option.selected = true;
                        e.target.appendChild(option);
                    } else {
                        e.target.value = '';
                    }
                }
            });
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing LocationLoader...');
    new LocationLoader();
});
