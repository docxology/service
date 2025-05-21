from dataclasses import dataclass, field
from typing import List, Optional, Union
import xml.etree.ElementTree as ET
from enum import Enum

# --- Helper functions for safer XML parsing ---
def safe_float(value: Optional[str], default: float = 0.0) -> float:
    """Safely convert a string to float with a default value on error."""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert '{value}' to float. Using default {default}.")
        return default

def safe_int(value: Optional[str], default: int = 0) -> int:
    """Safely convert a string to int with a default value on error."""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        print(f"Warning: Could not convert '{value}' to int. Using default {default}.")
        return default

def safe_enum_convert(value: Optional[str], enum_class: type, default_value) -> any:
    """Safely convert a string to an enum value with a default on error."""
    if value is None:
        return default_value
    try:
        return enum_class(value)
    except (ValueError, TypeError):
        print(f"Warning: '{value}' is not a valid {enum_class.__name__}. Using default {default_value.value}.")
        return default_value

def safe_find_text(element: Optional[ET.Element], tag_name: str, default: str = "") -> str:
    """Safely get text from an element's child, handling None elements."""
    if element is None:
        return default
    child = element.find(tag_name)
    return child.text if child is not None and child.text else default

# --- Enums for controlled vocabularies ---

class Currency(Enum):
    USD = "USD"
    DAI = "DAI"
    USDC = "USDC"
    # Add other currencies as needed

class PriceFrequency(Enum):
    MONTHLY = "monthly"
    ANNUALLY = "annually"
    # Add other frequencies as needed

class TermUnit(Enum):
    MONTHS = "months"
    YEARS = "years"
    # Add other units as needed

# --- Generic Pricing Components ---

@dataclass
class Price:
    amount: float
    currency: Currency

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return None
        amount = safe_float(element.text)
        currency = safe_enum_convert(element.get("currency"), Currency, Currency.USD)
        return cls(amount=amount, currency=currency)

    def to_element(self, tag_name: str) -> ET.Element:
        element = ET.Element(tag_name, {"currency": self.currency.value})
        element.text = str(self.amount)
        return element

@dataclass
class RecurringPrice(Price):
    frequency: PriceFrequency

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return None
        amount = safe_float(element.text)
        currency = safe_enum_convert(element.get("currency"), Currency, Currency.USD)
        frequency = safe_enum_convert(element.get("frequency"), PriceFrequency, PriceFrequency.MONTHLY)
        return cls(amount=amount, currency=currency, frequency=frequency)

    def to_element(self, tag_name: str) -> ET.Element:
        element = ET.Element(tag_name, {
            "currency": self.currency.value,
            "frequency": self.frequency.value
        })
        element.text = str(self.amount)
        return element


@dataclass
class RangeFee:
    min_amount: float
    max_amount: float
    currency: Currency
    description: Optional[str] = None # Text content of the RangeFee element

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return None
        min_amount = safe_float(element.get("min", "0"))
        max_amount = safe_float(element.get("max", "0"))
        currency = safe_enum_convert(element.get("currency"), Currency, Currency.USD)
        description = element.text
        return cls(min_amount=min_amount, max_amount=max_amount, currency=currency, description=description)

    def to_element(self, tag_name: str) -> ET.Element:
        element = ET.Element(tag_name, {
            "min": str(self.min_amount),
            "max": str(self.max_amount),
            "currency": self.currency.value
        })
        element.text = self.description
        return element

@dataclass
class CustomQuote:
    description: str

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return None
        return cls(description=element.text or "")

    def to_element(self, tag_name: str) -> ET.Element:
        element = ET.Element(tag_name)
        element.text = self.description
        return element

@dataclass
class Discount:
    condition: str
    amount: Price # Re-using Price for amount and currency

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return None
        condition_el = element.find("Condition")
        condition = condition_el.text if condition_el is not None and condition_el.text else ""
        
        amount_el = element.find("Amount")
        amount_val = float(amount_el.text) if amount_el is not None and amount_el.text else 0.0
        currency_val = Currency(amount_el.get("currency", "USD")) if amount_el is not None else Currency.USD
        
        return cls(condition=condition, amount=Price(amount=amount_val, currency=currency_val))

    def to_element(self) -> ET.Element:
        element = ET.Element("Discount")
        condition_el = ET.SubElement(element, "Condition")
        condition_el.text = self.condition
        amount_el = self.amount.to_element("Amount")
        element.append(amount_el)
        return element

@dataclass
class TierPricing:
    base_price: Optional[Price] = None
    discounts: List[Discount] = field(default_factory=list)

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return cls() # Return empty if no pricing info
        
        base_price_el = element.find("BasePrice")
        base_price = Price.from_element(base_price_el) if base_price_el is not None else None
        
        discounts_el = element.find("Discounts")
        discounts = []
        if discounts_el is not None:
            discounts = [Discount.from_element(disc_el) for disc_el in discounts_el.findall("Discount")]
            discounts = [d for d in discounts if d is not None] # Filter out None if parsing failed

        return cls(base_price=base_price, discounts=discounts)

    def to_element(self) -> ET.Element:
        element = ET.Element("Pricing")
        if self.base_price:
            element.append(self.base_price.to_element("BasePrice"))
        
        if self.discounts:
            discounts_el = ET.SubElement(element, "Discounts")
            for discount in self.discounts:
                discounts_el.append(discount.to_element())
        return element


@dataclass
class RetainerPricing:
    recurring_price: Optional[RecurringPrice] = None
    minimum_term_months: Optional[int] = None # Assuming unit is always months based on XML
    minimum_term_unit: Optional[TermUnit] = None


    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return cls()

        recurring_price_el = element.find("RecurringPrice")
        recurring_price = RecurringPrice.from_element(recurring_price_el) if recurring_price_el is not None else None
        
        min_term_el = element.find("MinimumTerm")
        minimum_term_months = None
        minimum_term_unit = None
        if min_term_el is not None and min_term_el.text:
            minimum_term_months = int(min_term_el.text)
            unit_attr = min_term_el.get("unit")
            if unit_attr:
                try:
                    minimum_term_unit = TermUnit(unit_attr)
                except ValueError:
                    print(f"Warning: Unknown MinimumTerm unit '{unit_attr}'. Defaulting to None.")


        return cls(recurring_price=recurring_price, minimum_term_months=minimum_term_months, minimum_term_unit=minimum_term_unit)

    def to_element(self) -> ET.Element:
        element = ET.Element("Pricing")
        if self.recurring_price:
            element.append(self.recurring_price.to_element("RecurringPrice"))
        if self.minimum_term_months is not None and self.minimum_term_unit is not None:
            min_term_el = ET.SubElement(element, "MinimumTerm", {"unit": self.minimum_term_unit.value})
            min_term_el.text = str(self.minimum_term_months)
        return element

@dataclass
class ModulePricing:
    setup_fee: Optional[Price] = None
    recurring_fee: Optional[RecurringPrice] = None
    per_session_fee: Optional[Price] = None
    range_fee: Optional[RangeFee] = None
    custom_quote: Optional[CustomQuote] = None

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return cls()
        
        setup_fee = Price.from_element(element.find("SetupFee"))
        recurring_fee = RecurringPrice.from_element(element.find("RecurringFee"))
        per_session_fee = Price.from_element(element.find("PerSessionFee"))
        range_fee = RangeFee.from_element(element.find("RangeFee"))
        custom_quote = CustomQuote.from_element(element.find("CustomQuote"))
        
        return cls(
            setup_fee=setup_fee,
            recurring_fee=recurring_fee,
            per_session_fee=per_session_fee,
            range_fee=range_fee,
            custom_quote=custom_quote
        )

    def to_element(self) -> ET.Element:
        element = ET.Element("Pricing")
        if self.setup_fee:
            element.append(self.setup_fee.to_element("SetupFee"))
        if self.recurring_fee:
            element.append(self.recurring_fee.to_element("RecurringFee"))
        if self.per_session_fee:
            element.append(self.per_session_fee.to_element("PerSessionFee"))
        if self.range_fee:
            element.append(self.range_fee.to_element("RangeFee"))
        if self.custom_quote:
            element.append(self.custom_quote.to_element("CustomQuote"))
        return element

# --- Core Service Structure Components ---

@dataclass
class Metadata:
    id: str
    name: str
    category: str
    description: str
    keywords: List[str] = field(default_factory=list)

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            raise ValueError("Metadata element cannot be None")
        
        # Helper to get text or default
        get_text = lambda el_name, default="": element.findtext(el_name, default=default)

        id_val = get_text("id")
        name_val = get_text("Name")
        category_val = get_text("Category")
        description_val = get_text("Description")
        keywords_str = get_text("Keywords")
        keywords_list = [k.strip() for k in keywords_str.split(',') if k.strip()] if keywords_str else []
        
        return cls(id=id_val, name=name_val, category=category_val, description=description_val, keywords=keywords_list)

    def to_element(self) -> ET.Element:
        element = ET.Element("Metadata")
        ET.SubElement(element, "id").text = self.id
        ET.SubElement(element, "Name").text = self.name
        ET.SubElement(element, "Category").text = self.category
        ET.SubElement(element, "Description").text = self.description
        ET.SubElement(element, "Keywords").text = ",".join(self.keywords)
        return element

@dataclass
class Provider:
    name: str
    contact_person: Optional[str] = None
    website: Optional[str] = None

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            # Default provider if not specified, or handle as error
            return cls(name="Unknown Provider") 
        
        get_text = lambda el_name, default=None: element.findtext(el_name, default=default)
        
        name_val = get_text("Name", "Unknown Provider")
        contact_person_val = get_text("ContactPerson")
        website_val = get_text("Website")
        
        return cls(name=name_val, contact_person=contact_person_val, website=website_val)

    def to_element(self) -> ET.Element:
        element = ET.Element("Provider")
        ET.SubElement(element, "Name").text = self.name
        if self.contact_person:
            ET.SubElement(element, "ContactPerson").text = self.contact_person
        if self.website:
            ET.SubElement(element, "Website").text = self.website
        return element

@dataclass
class ExampleWork:
    name: str
    url: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return None
        
        get_text = lambda el_name, default=None: element.findtext(el_name, default=default)

        name_val = get_text("Name", "N/A")
        url_val = get_text("URL")
        description_val = get_text("Description")
        date_val = get_text("Date")

        return cls(name=name_val, url=url_val, description=description_val, date=date_val)

    def to_element(self) -> ET.Element:
        element = ET.Element("Example")
        ET.SubElement(element, "Name").text = self.name
        if self.url:
            ET.SubElement(element, "URL").text = self.url
        if self.description:
            ET.SubElement(element, "Description").text = self.description
        if self.date:
            ET.SubElement(element, "Date").text = self.date
        return element

@dataclass
class PreviousWork:
    examples: List[ExampleWork] = field(default_factory=list)

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return cls() # Return empty PreviousWork if element is not found
        
        examples = [ExampleWork.from_element(ex_el) for ex_el in element.findall("Example")]
        examples = [ex for ex in examples if ex is not None] # Filter out None results
        return cls(examples=examples)
    
    def to_element(self) -> ET.Element:
        element = ET.Element("PreviousWork")
        for example in self.examples:
            element.append(example.to_element())
        return element


@dataclass
class Tier:
    id: str
    name: str
    description: str
    deliverables: List[str] = field(default_factory=list)
    pricing: TierPricing = field(default_factory=TierPricing)
    previous_work: Optional[PreviousWork] = None # As seen in 1.2.2

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            raise ValueError("Tier element cannot be None")

        get_text = lambda el_name, default="": element.findtext(el_name, default=default)

        id_val = get_text("id")
        name_val = get_text("Name")
        description_val = get_text("Description")
        
        deliverables_el = element.find("Deliverables")
        deliverables = []
        if deliverables_el is not None:
            deliverables = [d.text for d in deliverables_el.findall("Deliverable") if d.text]
            
        pricing_el = element.find("Pricing")
        pricing = TierPricing.from_element(pricing_el) if pricing_el is not None else TierPricing() # Ensure pricing object exists

        previous_work_el = element.find("PreviousWork")
        previous_work = PreviousWork.from_element(previous_work_el) if previous_work_el is not None else None
        
        return cls(
            id=id_val, 
            name=name_val, 
            description=description_val, 
            deliverables=deliverables, 
            pricing=pricing,
            previous_work=previous_work
        )

    def to_element(self) -> ET.Element:
        element = ET.Element("Tier")
        ET.SubElement(element, "id").text = self.id
        ET.SubElement(element, "Name").text = self.name
        ET.SubElement(element, "Description").text = self.description
        
        deliverables_el = ET.SubElement(element, "Deliverables")
        for deliverable in self.deliverables:
            ET.SubElement(deliverables_el, "Deliverable").text = deliverable
            
        element.append(self.pricing.to_element())

        if self.previous_work:
            element.append(self.previous_work.to_element())
            
        return element


@dataclass
class Package:
    id: str
    name: str
    description: str
    tiers: List[Tier] = field(default_factory=list)
    previous_work: Optional[PreviousWork] = None # As seen in 2.2.1 (package-level previous work)

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            raise ValueError("Package element cannot be None")

        get_text = lambda el_name, default="": element.findtext(el_name, default=default)

        id_val = get_text("id")
        name_val = get_text("Name")
        description_val = get_text("Description")
        
        tiers_el = element.find("Tiers")
        tiers_list = []
        if tiers_el is not None:
            tiers_list = [Tier.from_element(tier_el) for tier_el in tiers_el.findall("Tier")]
        
        previous_work_el = element.find("PreviousWork")
        previous_work = PreviousWork.from_element(previous_work_el) if previous_work_el is not None else None

        return cls(id=id_val, name=name_val, description=description_val, tiers=tiers_list, previous_work=previous_work)

    def to_element(self) -> ET.Element:
        element = ET.Element("Package")
        ET.SubElement(element, "id").text = self.id
        ET.SubElement(element, "Name").text = self.name
        ET.SubElement(element, "Description").text = self.description
        
        tiers_el = ET.SubElement(element, "Tiers")
        for tier_obj in self.tiers:
            tiers_el.append(tier_obj.to_element())
        
        if self.previous_work:
            element.append(self.previous_work.to_element())
            
        return element

@dataclass
class ClientInfo:
    name: str
    position: Optional[str] = None
    company: Optional[str] = None

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return cls(name="Anonymous") # Default if not found
        
        get_text = lambda el_name, default=None: element.findtext(el_name, default=default)
        name_val = get_text("Name", "Anonymous")
        position_val = get_text("Position")
        company_val = get_text("Company")
        return cls(name=name_val, position=position_val, company=company_val)

    def to_element(self) -> ET.Element:
        element = ET.Element("ClientInfo")
        ET.SubElement(element, "Name").text = self.name
        if self.position:
            ET.SubElement(element, "Position").text = self.position
        if self.company:
            ET.SubElement(element, "Company").text = self.company
        return element

@dataclass
class Testimonial:
    client_info: ClientInfo
    quote: str
    date: Optional[str] = None

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return None
        
        client_info_el = element.find("ClientInfo")
        client_info = ClientInfo.from_element(client_info_el) if client_info_el is not None else ClientInfo(name="Unknown")

        quote_el = element.find("Quote")
        quote = quote_el.text if quote_el is not None and quote_el.text else ""
        
        date_el = element.find("Date")
        date_str = date_el.text if date_el is not None and date_el.text else None
        
        return cls(client_info=client_info, quote=quote, date=date_str)

    def to_element(self) -> ET.Element:
        element = ET.Element("Testimonial")
        element.append(self.client_info.to_element())
        ET.SubElement(element, "Quote").text = self.quote
        if self.date:
            ET.SubElement(element, "Date").text = self.date
        return element

@dataclass
class AddOnModule:
    id: str
    name: str
    description: str
    pricing: ModulePricing = field(default_factory=ModulePricing)
    deliverables: List[str] = field(default_factory=list)

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            raise ValueError("AddOnModule element cannot be None")

        get_text = lambda el_name, default="": element.findtext(el_name, default=default)
        id_val = get_text("id")
        name_val = get_text("Name")
        description_val = get_text("Description")

        pricing_el = element.find("Pricing")
        pricing = ModulePricing.from_element(pricing_el) if pricing_el is not None else ModulePricing()

        deliverables_el = element.find("Deliverables")
        deliverables = []
        if deliverables_el is not None:
            deliverables = [d.text for d in deliverables_el.findall("Deliverable") if d.text]
            
        return cls(id=id_val, name=name_val, description=description_val, pricing=pricing, deliverables=deliverables)

    def to_element(self) -> ET.Element:
        element = ET.Element("Module") # Note: XML tag is "Module"
        ET.SubElement(element, "id").text = self.id
        ET.SubElement(element, "Name").text = self.name
        ET.SubElement(element, "Description").text = self.description
        element.append(self.pricing.to_element())

        if self.deliverables:
            deliverables_el = ET.SubElement(element, "Deliverables")
            for deliverable_text in self.deliverables:
                ET.SubElement(deliverables_el, "Deliverable").text = deliverable_text
        return element


@dataclass
class Retainer:
    id: str
    name: str
    description: str
    services: List[str] = field(default_factory=list) # These are <Service> text elements within <Services>
    pricing: RetainerPricing = field(default_factory=RetainerPricing)
    add_on_modules: List[AddOnModule] = field(default_factory=list)
    testimonials: List[Testimonial] = field(default_factory=list)

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            raise ValueError("Retainer element cannot be None")

        get_text = lambda el_name, default="": element.findtext(el_name, default=default)
        id_val = get_text("id")
        name_val = get_text("Name")
        description_val = get_text("Description")

        services_list_el = element.find("Services")
        services_items = []
        if services_list_el is not None:
            services_items = [s.text for s in services_list_el.findall("Service") if s.text] # Renamed for clarity

        pricing_el = element.find("Pricing")
        pricing = RetainerPricing.from_element(pricing_el) if pricing_el is not None else RetainerPricing()

        add_ons_el = element.find("AddOnModules")
        add_on_modules_list = []
        if add_ons_el is not None:
            add_on_modules_list = [AddOnModule.from_element(mod_el) for mod_el in add_ons_el.findall("Module")]
            add_on_modules_list = [m for m in add_on_modules_list if m is not None]


        testimonials_el = element.find("Testimonials")
        testimonials_list = []
        if testimonials_el is not None:
            testimonials_list = [Testimonial.from_element(test_el) for test_el in testimonials_el.findall("Testimonial")]
            testimonials_list = [t for t in testimonials_list if t is not None]


        return cls(
            id=id_val, 
            name=name_val, 
            description=description_val, 
            services=services_items, 
            pricing=pricing,
            add_on_modules=add_on_modules_list,
            testimonials=testimonials_list
        )

    def to_element(self) -> ET.Element:
        element = ET.Element("Retainer")
        ET.SubElement(element, "id").text = self.id
        ET.SubElement(element, "Name").text = self.name
        ET.SubElement(element, "Description").text = self.description

        services_list_el = ET.SubElement(element, "Services")
        for service_item_text in self.services:
            ET.SubElement(services_list_el, "Service").text = service_item_text # Naming consistent with XML

        element.append(self.pricing.to_element())

        if self.add_on_modules:
            add_ons_el = ET.SubElement(element, "AddOnModules")
            for module_obj in self.add_on_modules:
                add_ons_el.append(module_obj.to_element())
        
        if self.testimonials:
            testimonials_el = ET.SubElement(element, "Testimonials")
            for testimonial_obj in self.testimonials:
                testimonials_el.append(testimonial_obj.to_element())
        return element

@dataclass
class Offering:
    packages: List[Package] = field(default_factory=list)
    retainers: List[Retainer] = field(default_factory=list)

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            return cls() # Return empty offering

        packages = [Package.from_element(pkg_el) for pkg_el in element.findall("Package")]
        retainers = [Retainer.from_element(ret_el) for ret_el in element.findall("Retainer")]
        return cls(packages=packages, retainers=retainers)

    def to_element(self) -> ET.Element:
        element = ET.Element("Offering")
        for package_obj in self.packages:
            element.append(package_obj.to_element())
        for retainer_obj in self.retainers:
            element.append(retainer_obj.to_element())
        return element


@dataclass
class Service: # This is the top-level Service (e.g., Governance, Knowledge)
    metadata: Metadata
    provider: Provider
    offering: Offering

    @classmethod
    def from_element(cls, element: Optional[ET.Element]):
        if element is None:
            raise ValueError("Service element cannot be None")

        metadata_el = element.find("Metadata")
        if metadata_el is None:
            raise ValueError("Service must have Metadata")
        metadata = Metadata.from_element(metadata_el)

        provider_el = element.find("Provider")
        # Provider can be optional or have defaults if not strictly required by schema
        provider = Provider.from_element(provider_el) if provider_el is not None else Provider(name="Default Provider")


        offering_el = element.find("Offering")
        offering = Offering.from_element(offering_el) if offering_el is not None else Offering()
        
        return cls(metadata=metadata, provider=provider, offering=offering)

    def to_element(self) -> ET.Element:
        element = ET.Element("Service")
        element.append(self.metadata.to_element())
        element.append(self.provider.to_element())
        element.append(self.offering.to_element())
        return element

@dataclass
class ServiceCatalog:
    services: List[Service] = field(default_factory=list)
    xml_namespace: str = "https://www.clinamenic.com/schemas/services/v1"

    def load_from_xml(self, file_path: str):
        """Loads service data from an XML file."""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            # Handle namespace if present
            namespace_map = {}
            if '}' in root.tag:
                self.xml_namespace = root.tag.split('}')[0][1:] # Extract from root tag like {namespace}Services
                namespace_map = {'ns': self.xml_namespace}

            self.services = []
            service_elements = root.findall("ns:Service", namespace_map) if namespace_map else root.findall("Service")

            for service_el in service_elements:
                try:
                    self.services.append(Service.from_element(service_el))
                except ValueError as e:
                    print(f"Skipping a service due to parsing error: {e}")
        except FileNotFoundError:
            print(f"Error: XML file not found at {file_path}")
            self.services = []
        except ET.ParseError:
            print(f"Error: Could not parse XML file at {file_path}")
            self.services = []

    def to_xml_string(self, pretty_print: bool = True) -> str:
        """Serializes the service catalog to an XML string."""
        root_attrs = {}
        if self.xml_namespace:
             # For ET, register_namespace is for QName generation, not default ns on root
            ET.register_namespace('', self.xml_namespace) # For cleaner output
            root_attrs["xmlns"] = self.xml_namespace

        root = ET.Element("Services", root_attrs)
        
        for service_obj in self.services:
            root.append(service_obj.to_element())
        
        if pretty_print:
            ET.indent(root, space="  ")
            
        return ET.tostring(root, encoding="unicode", xml_declaration=True)

    def save_to_xml(self, file_path: str, pretty_print: bool = True):
        """Saves the service catalog to an XML file."""
        xml_string = self.to_xml_string(pretty_print)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_string)

    # --- Methods for managing services (CRUD operations) ---
    def add_service(self, service: Service):
        """Add a new service to the catalog."""
        self.services.append(service)

    def get_service_by_id(self, service_id: str) -> Optional[Service]:
        """Find a service by its ID."""
        for service in self.services:
            if service.metadata.id == service_id:
                return service
        return None

    def get_service_by_name(self, service_name: str) -> Optional[Service]:
        """Find a service by its name (case-insensitive)."""
        for service in self.services:
            if service.metadata.name.lower() == service_name.lower():
                return service
        return None

    def update_service(self, service_id: str, updated_service: Service) -> bool:
        """Replace a service with an updated version."""
        for i, service in enumerate(self.services):
            if service.metadata.id == service_id:
                self.services[i] = updated_service
                return True
        return False

    def delete_service(self, service_id: str) -> bool:
        """Remove a service from the catalog by ID."""
        service_to_delete = self.get_service_by_id(service_id)
        if service_to_delete:
            self.services.remove(service_to_delete)
            return True
        return False

    # --- Advanced service operations ---
    def clone_service(self, service_id: str, new_id: Optional[str] = None,
                     new_name: Optional[str] = None) -> Optional[Service]:
        """Create a copy of an existing service with optional new ID and name."""
        import copy
        service = self.get_service_by_id(service_id)
        if not service:
            return None
            
        # Deep copy to avoid modifying the original
        cloned_service = copy.deepcopy(service)
        
        # Update ID and name if provided
        if new_id:
            cloned_service.metadata.id = new_id
        if new_name:
            cloned_service.metadata.name = new_name
            
        return cloned_service
        
    def merge_services(self, primary_id: str, secondary_id: str, 
                      merge_strategy: str = "append") -> Optional[Service]:
        """
        Merge two services into one. The primary service is kept, and the secondary's
        packages and retainers are added to it.
        
        Args:
            primary_id: ID of the service to keep and augment
            secondary_id: ID of the service to merge into the primary
            merge_strategy: How to handle conflicts ("append", "replace", "skip")
        
        Returns:
            The merged service or None if either service isn't found
        """
        primary = self.get_service_by_id(primary_id)
        secondary = self.get_service_by_id(secondary_id)
        
        if not primary or not secondary:
            return None
            
        # Create a new merged service based on the primary
        import copy
        merged = copy.deepcopy(primary)
        
        # Add secondary's packages
        for package in secondary.offering.packages:
            # Simple append strategy for now
            merged.offering.packages.append(copy.deepcopy(package))
            
        # Add secondary's retainers
        for retainer in secondary.offering.retainers:
            merged.offering.retainers.append(copy.deepcopy(retainer))
            
        return merged

    # --- Validation/Checker methods ---
    def validate_catalog(self) -> List[str]:
        """Performs basic validation checks on the catalog."""
        errors = []
        service_ids = set()
        for i, service in enumerate(self.services):
            if not service.metadata.id:
                errors.append(f"Service at index {i} is missing an ID.")
            elif service.metadata.id in service_ids:
                errors.append(f"Duplicate service ID found: {service.metadata.id}")
            else:
                service_ids.add(service.metadata.id)
            
            if not service.metadata.name:
                errors.append(f"Service '{service.metadata.id}' is missing a Name in Metadata.")

            # Example: Validate package IDs within each service
            package_ids = set()
            for pkg_idx, package in enumerate(service.offering.packages):
                if not package.id:
                    errors.append(f"Service '{service.metadata.id}', Package at index {pkg_idx} is missing an ID.")
                elif package.id in package_ids:
                    errors.append(f"Service '{service.metadata.id}', Duplicate package ID found: {package.id}")
                else:
                    package_ids.add(package.id)
                
                # Further validation for tiers, etc. can be added here.
                tier_ids = set()
                for tier_idx, tier in enumerate(package.tiers):
                    if not tier.id:
                        errors.append(f"Service '{service.metadata.id}', Package '{package.id}', Tier at index {tier_idx} missing ID.")
                    elif tier.id in tier_ids:
                         errors.append(f"Service '{service.metadata.id}', Package '{package.id}', Duplicate tier ID: {tier.id}")
                    else:
                        tier_ids.add(tier.id)
                    if tier.pricing.base_price is None and not tier.pricing.discounts: # Example check
                        pass # Tiers might not always have a base price if they have only discounts or are custom.
                        # This depends on business logic. For now, allow it.
                        # errors.append(f"Service '{service.metadata.id}', Package '{package.id}', Tier '{tier.id}' has no base price.")

        return errors
        
    def validate_ids(self) -> List[str]:
        """Check that all IDs follow a consistent format."""
        errors = []
        
        # Check service IDs are numeric
        for service in self.services:
            try:
                service_num = int(service.metadata.id)
                if service_num <= 0:
                    errors.append(f"Service ID '{service.metadata.id}' should be a positive integer.")
            except ValueError:
                errors.append(f"Service ID '{service.metadata.id}' should be numeric.")
                
            # Check package IDs are of form service_id.n
            for pkg in service.offering.packages:
                parts = pkg.id.split('.')
                if len(parts) != 2:
                    errors.append(f"Package ID '{pkg.id}' should be of format 'service_id.n'.")
                elif parts[0] != service.metadata.id:
                    errors.append(f"Package ID '{pkg.id}' should start with service ID '{service.metadata.id}'.")
                
                # Check tier IDs are of form package_id.n
                for tier in pkg.tiers:
                    parts = tier.id.split('.')
                    if len(parts) != 3:
                        errors.append(f"Tier ID '{tier.id}' should be of format 'service_id.package_num.tier_num'.")
                    elif f"{parts[0]}.{parts[1]}" != pkg.id:
                        errors.append(f"Tier ID '{tier.id}' should start with package ID '{pkg.id}'.")
                        
        return errors

    # --- Transform/extraction methods ---
    def to_dict(self) -> dict:
        """Convert the service catalog to a nested dictionary structure."""
        result = {
            "services": []
        }
        
        for service in self.services:
            # Convert service to dict
            service_dict = {
                "id": service.metadata.id,
                "name": service.metadata.name,
                "category": service.metadata.category,
                "description": service.metadata.description,
                "keywords": service.metadata.keywords,
                "provider": {
                    "name": service.provider.name,
                    "contact_person": service.provider.contact_person,
                    "website": service.provider.website
                },
                "packages": [],
                "retainers": []
            }
            
            # Add packages
            for pkg in service.offering.packages:
                pkg_dict = {
                    "id": pkg.id,
                    "name": pkg.name,
                    "description": pkg.description,
                    "tiers": []
                }
                
                # Add tiers
                for tier in pkg.tiers:
                    tier_dict = {
                        "id": tier.id,
                        "name": tier.name,
                        "description": tier.description,
                        "deliverables": tier.deliverables
                    }
                    
                    # Add pricing if available
                    if tier.pricing.base_price:
                        tier_dict["base_price"] = {
                            "amount": tier.pricing.base_price.amount,
                            "currency": tier.pricing.base_price.currency.value
                        }
                    
                    pkg_dict["tiers"].append(tier_dict)
                
                service_dict["packages"].append(pkg_dict)
            
            # Add retainers
            for retainer in service.offering.retainers:
                retainer_dict = {
                    "id": retainer.id,
                    "name": retainer.name,
                    "description": retainer.description,
                    "services": retainer.services
                }
                
                # Add pricing if available
                if retainer.pricing.recurring_price:
                    retainer_dict["pricing"] = {
                        "amount": retainer.pricing.recurring_price.amount,
                        "currency": retainer.pricing.recurring_price.currency.value,
                        "frequency": retainer.pricing.recurring_price.frequency.value
                    }
                    if retainer.pricing.minimum_term_months:
                        retainer_dict["pricing"]["minimum_term"] = {
                            "value": retainer.pricing.minimum_term_months,
                            "unit": retainer.pricing.minimum_term_unit.value if retainer.pricing.minimum_term_unit else "months"
                        }
                
                service_dict["retainers"].append(retainer_dict)
            
            result["services"].append(service_dict)
            
        return result
        
    def export_to_json(self, file_path: str) -> None:
        """Export the service catalog to a JSON file."""
        import json
        
        # Use the to_dict method to get a JSON-serializable representation
        catalog_dict = self.to_dict()
        
        # Write to JSON file
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(catalog_dict, f, indent=2, ensure_ascii=False)
    
    def export_to_csv(self, directory_path: str) -> dict:
        """
        Export services, packages, and tiers to separate CSV files.
        Returns a dictionary with the paths to the generated files.
        """
        import csv
        import os
        
        if not os.path.exists(directory_path):
            os.makedirs(directory_path)
            
        # Prepare the file paths
        service_csv = os.path.join(directory_path, "services.csv")
        package_csv = os.path.join(directory_path, "packages.csv")
        tier_csv = os.path.join(directory_path, "tiers.csv")
        retainer_csv = os.path.join(directory_path, "retainers.csv")
        
        # Write services CSV
        with open(service_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Name", "Category", "Description", "Keywords", "Provider"])
            
            for service in self.services:
                keywords_str = ",".join(service.metadata.keywords)
                provider_str = service.provider.name
                writer.writerow([
                    service.metadata.id,
                    service.metadata.name,
                    service.metadata.category,
                    service.metadata.description,
                    keywords_str,
                    provider_str
                ])
        
        # Write packages CSV
        with open(package_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Service ID", "Name", "Description"])
            
            for service in self.services:
                for pkg in service.offering.packages:
                    writer.writerow([
                        pkg.id,
                        service.metadata.id,
                        pkg.name,
                        pkg.description
                    ])
        
        # Write tiers CSV
        with open(tier_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Package ID", "Name", "Description", "Base Price", "Currency"])
            
            for service in self.services:
                for pkg in service.offering.packages:
                    for tier in pkg.tiers:
                        base_price = tier.pricing.base_price.amount if tier.pricing.base_price else ""
                        currency = tier.pricing.base_price.currency.value if tier.pricing.base_price else ""
                        
                        writer.writerow([
                            tier.id,
                            pkg.id,
                            tier.name,
                            tier.description,
                            base_price,
                            currency
                        ])
        
        # Write retainers CSV
        with open(retainer_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Service ID", "Name", "Description", "Monthly Price", "Currency", "Min Term"])
            
            for service in self.services:
                for retainer in service.offering.retainers:
                    price = ""
                    currency = ""
                    min_term = ""
                    
                    if retainer.pricing.recurring_price:
                        price = retainer.pricing.recurring_price.amount
                        currency = retainer.pricing.recurring_price.currency.value
                    
                    if retainer.pricing.minimum_term_months:
                        min_term = f"{retainer.pricing.minimum_term_months} {retainer.pricing.minimum_term_unit.value if retainer.pricing.minimum_term_unit else 'months'}"
                    
                    writer.writerow([
                        retainer.id,
                        service.metadata.id,
                        retainer.name,
                        retainer.description,
                        price,
                        currency,
                        min_term
                    ])
                    
        return {
            "services": service_csv,
            "packages": package_csv,
            "tiers": tier_csv,
            "retainers": retainer_csv
        }
        
    # --- Reporting methods ---
    def get_price_summary(self) -> dict:
        """Generate a summary of pricing across all services."""
        summary = {
            "package_tiers": {
                "count": 0,
                "price_range": {"min": float('inf'), "max": 0, "currency": "USD"},
                "avg_price": 0,
                "prices_by_currency": {}
            },
            "retainers": {
                "count": 0,
                "price_range": {"min": float('inf'), "max": 0, "currency": "USD"},
                "avg_price": 0,
                "prices_by_currency": {}
            }
        }
        
        # Track all prices for averaging
        all_tier_prices = []
        all_retainer_prices = []
        
        # Process package tiers
        for service in self.services:
            for pkg in service.offering.packages:
                for tier in pkg.tiers:
                    if tier.pricing.base_price:
                        summary["package_tiers"]["count"] += 1
                        price = tier.pricing.base_price.amount
                        currency = tier.pricing.base_price.currency.value
                        
                        # Add to currency-specific tracking
                        if currency not in summary["package_tiers"]["prices_by_currency"]:
                            summary["package_tiers"]["prices_by_currency"][currency] = {
                                "count": 0, "min": float('inf'), "max": 0, "sum": 0
                            }
                        
                        curr_stats = summary["package_tiers"]["prices_by_currency"][currency]
                        curr_stats["count"] += 1
                        curr_stats["min"] = min(curr_stats["min"], price)
                        curr_stats["max"] = max(curr_stats["max"], price)
                        curr_stats["sum"] += price
                        
                        # Store price for averaging later
                        all_tier_prices.append((price, currency))
            
            # Process retainers
            for retainer in service.offering.retainers:
                if retainer.pricing.recurring_price:
                    summary["retainers"]["count"] += 1
                    price = retainer.pricing.recurring_price.amount
                    currency = retainer.pricing.recurring_price.currency.value
                    
                    # Add to currency-specific tracking
                    if currency not in summary["retainers"]["prices_by_currency"]:
                        summary["retainers"]["prices_by_currency"][currency] = {
                            "count": 0, "min": float('inf'), "max": 0, "sum": 0
                        }
                    
                    curr_stats = summary["retainers"]["prices_by_currency"][currency]
                    curr_stats["count"] += 1
                    curr_stats["min"] = min(curr_stats["min"], price)
                    curr_stats["max"] = max(curr_stats["max"], price)
                    curr_stats["sum"] += price
                    
                    # Store price for averaging
                    all_retainer_prices.append((price, currency))
        
        # Calculate global min, max, avg for tiers if we have data
        if all_tier_prices:
            # For simplicity, use the most common currency for the global stats
            from collections import Counter
            currencies = Counter([c for _, c in all_tier_prices])
            main_currency = currencies.most_common(1)[0][0]
            
            # Filter and process prices in the main currency
            main_prices = [p for p, c in all_tier_prices if c == main_currency]
            if main_prices:
                summary["package_tiers"]["price_range"]["min"] = min(main_prices)
                summary["package_tiers"]["price_range"]["max"] = max(main_prices)
                summary["package_tiers"]["price_range"]["currency"] = main_currency
                summary["package_tiers"]["avg_price"] = sum(main_prices) / len(main_prices)
        
        # Calculate averages for each currency in tier prices
        for currency, stats in summary["package_tiers"]["prices_by_currency"].items():
            if stats["count"] > 0:
                stats["avg"] = stats["sum"] / stats["count"]
            # Clean up temporary sum value
            del stats["sum"]
        
        # Calculate global min, max, avg for retainers if we have data
        if all_retainer_prices:
            from collections import Counter
            currencies = Counter([c for _, c in all_retainer_prices])
            main_currency = currencies.most_common(1)[0][0]
            
            main_prices = [p for p, c in all_retainer_prices if c == main_currency]
            if main_prices:
                summary["retainers"]["price_range"]["min"] = min(main_prices)
                summary["retainers"]["price_range"]["max"] = max(main_prices)
                summary["retainers"]["price_range"]["currency"] = main_currency
                summary["retainers"]["avg_price"] = sum(main_prices) / len(main_prices)
        
        # Calculate averages for each currency in retainer prices
        for currency, stats in summary["retainers"]["prices_by_currency"].items():
            if stats["count"] > 0:
                stats["avg"] = stats["sum"] / stats["count"]
            # Clean up temporary sum value
            del stats["sum"]
            
        return summary
    
    def generate_service_report(self) -> dict:
        """Generate a comprehensive report about the service catalog."""
        report = {
            "total_services": len(self.services),
            "total_packages": sum(len(service.offering.packages) for service in self.services),
            "total_tiers": sum(sum(len(package.tiers) for package in service.offering.packages) 
                              for service in self.services),
            "total_retainers": sum(len(service.offering.retainers) for service in self.services),
            "services_by_category": {},
            "packages_per_service": [],
            "tiers_per_package": [],
            "price_summary": self.get_price_summary(),
            "keyword_frequency": {}
        }
        
        # Calculate services by category
        for service in self.services:
            category = service.metadata.category
            if category not in report["services_by_category"]:
                report["services_by_category"][category] = 0
            report["services_by_category"][category] += 1
            
            # Calculate packages per service
            package_count = len(service.offering.packages)
            report["packages_per_service"].append({
                "service_id": service.metadata.id,
                "service_name": service.metadata.name,
                "package_count": package_count
            })
            
            # Track keyword frequency
            for keyword in service.metadata.keywords:
                if keyword not in report["keyword_frequency"]:
                    report["keyword_frequency"][keyword] = 0
                report["keyword_frequency"][keyword] += 1
            
            # Calculate tiers per package
            for package in service.offering.packages:
                tier_count = len(package.tiers)
                report["tiers_per_package"].append({
                    "package_id": package.id,
                    "package_name": package.name,
                    "tier_count": tier_count
                })
        
        # Sort keyword frequency
        report["keyword_frequency"] = dict(sorted(
            report["keyword_frequency"].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        return report
        
    # --- Visualization helpers ---
    def prepare_visualization_data(self) -> dict:
        """
        Prepare data structures optimized for visualization libraries.
        This returns data in formats that are easy to use with matplotlib, seaborn, etc.
        """
        # For hierarchical visualizations (e.g., treemaps, sunbursts)
        hierarchy_data = {
            "name": "Services",
            "children": []
        }
        
        # For price comparisons
        price_data = {
            "ids": [],
            "names": [],
            "prices": [],
            "currencies": []
        }
        
        # For service category distribution
        category_data = {}
        
        # Process services
        for service in self.services:
            # Add to hierarchy
            service_node = {
                "name": service.metadata.name,
                "children": []
            }
            
            # Track category
            category = service.metadata.category
            if category not in category_data:
                category_data[category] = 0
            category_data[category] += 1
            
            # Process packages
            for package in service.offering.packages:
                package_node = {
                    "name": package.name,
                    "children": []
                }
                
                # Process tiers
                for tier in package.tiers:
                    tier_node = {
                        "name": tier.name
                    }
                    
                    # Add price data if available
                    if tier.pricing.base_price:
                        tier_node["value"] = tier.pricing.base_price.amount
                        
                        # Also add to price comparison data
                        price_data["ids"].append(tier.id)
                        price_data["names"].append(f"{service.metadata.name} - {package.name} - {tier.name}")
                        price_data["prices"].append(tier.pricing.base_price.amount)
                        price_data["currencies"].append(tier.pricing.base_price.currency.value)
                    
                    package_node["children"].append(tier_node)
                
                service_node["children"].append(package_node)
            
            hierarchy_data["children"].append(service_node)
        
        return {
            "hierarchy": hierarchy_data,
            "prices": price_data,
            "categories": category_data
        }
    
    def export_for_d3(self, file_path: str) -> None:
        """Export data in a format suitable for D3.js visualizations."""
        import json
        
        visualization_data = self.prepare_visualization_data()
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(visualization_data["hierarchy"], f, indent=2)
            
    def generate_price_chart(self, output_path: str = "price_chart.png") -> str:
        """
        Generate a price comparison chart across all tiers.
        Requires matplotlib to be installed.
        
        Returns:
            Path to the generated image file
        """
        try:
            import matplotlib.pyplot as plt
            import numpy as np
        except ImportError:
            return "Error: matplotlib is required for chart generation. Install with 'pip install matplotlib'."
        
        # Get price data
        viz_data = self.prepare_visualization_data()
        price_data = viz_data["prices"]
        
        # Skip if no price data
        if not price_data["prices"]:
            return "No price data available for chart generation"
        
        # Filter to most common currency for meaningful comparison
        from collections import Counter
        currencies = Counter(price_data["currencies"])
        main_currency = currencies.most_common(1)[0][0]
        
        main_indices = [i for i, curr in enumerate(price_data["currencies"]) if curr == main_currency]
        main_names = [price_data["names"][i] for i in main_indices]
        main_prices = [price_data["prices"][i] for i in main_indices]
        
        # Create horizontal bar chart
        plt.figure(figsize=(10, max(5, len(main_names) * 0.4)))
        plt.barh(main_names, main_prices)
        plt.xlabel(f"Price ({main_currency})")
        plt.title("Service Tier Price Comparison")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return output_path
        
    def generate_category_chart(self, output_path: str = "category_chart.png") -> str:
        """
        Generate a pie chart of services by category.
        Requires matplotlib to be installed.
        
        Returns:
            Path to the generated image file
        """
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            return "Error: matplotlib is required for chart generation. Install with 'pip install matplotlib'."
        
        # Get category data
        viz_data = self.prepare_visualization_data()
        categories = viz_data["categories"]
        
        # Create pie chart
        plt.figure(figsize=(8, 8))
        plt.pie(
            categories.values(), 
            labels=categories.keys(),
            autopct='%1.1f%%', 
            startangle=90
        )
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
        plt.title("Services by Category")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
        
        return output_path

# --- Example Usage & Command Line Interface ---
if __name__ == "__main__":
    import sys
    import os
    import argparse
    
    # Default path for the service XML
    DEFAULT_XML_PATH = "clinamenic_service.xml"
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Process service catalog XML")
    
    # Add commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Load and validate command
    validate_parser = subparsers.add_parser("validate", help="Load and validate the service XML")
    validate_parser.add_argument("--xml", "-x", default=DEFAULT_XML_PATH, help="Path to the service XML file")
    validate_parser.add_argument("--check-ids", action="store_true", help="Check ID format consistency")
    
    # Convert command
    convert_parser = subparsers.add_parser("convert", help="Convert service XML to other formats")
    convert_parser.add_argument("--xml", "-x", default=DEFAULT_XML_PATH, help="Path to the service XML file")
    convert_parser.add_argument("--format", "-f", choices=["json", "csv"], required=True, help="Output format")
    convert_parser.add_argument("--output", "-o", required=True, help="Output file/directory path")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate reports about the service catalog")
    report_parser.add_argument("--xml", "-x", default=DEFAULT_XML_PATH, help="Path to the service XML file")
    report_parser.add_argument("--type", "-t", choices=["summary", "prices", "full"], default="summary", 
                             help="Type of report to generate")
    report_parser.add_argument("--output", "-o", help="Output file path (JSON format)")
    
    # Visualize command
    viz_parser = subparsers.add_parser("visualize", help="Generate data visualizations")
    viz_parser.add_argument("--xml", "-x", default=DEFAULT_XML_PATH, help="Path to the service XML file")
    viz_parser.add_argument("--type", "-t", choices=["prices", "categories", "d3"], required=True,
                           help="Type of visualization to generate")
    viz_parser.add_argument("--output", "-o", required=True, help="Output file path")
    
    # CRUD operations
    crud_parser = subparsers.add_parser("crud", help="Perform CRUD operations on the service catalog")
    crud_parser.add_argument("--xml", "-x", default=DEFAULT_XML_PATH, help="Path to the service XML file")
    crud_parser.add_argument("--operation", "-op", choices=["get", "add", "update", "delete", "list"], required=True,
                            help="Operation to perform")
    crud_parser.add_argument("--service-id", help="Service ID for operations that require it")
    crud_parser.add_argument("--json-input", help="JSON file with service data for add/update operations")
    crud_parser.add_argument("--output", "-o", help="Output file for saving modified XML")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Create the catalog instance
    catalog = ServiceCatalog()
    
    # Handle commands
    if args.command == "validate":
        xml_path = args.xml
        print(f"Loading service catalog from: {xml_path}")
        
        try:
            catalog.load_from_xml(xml_path)
            print(f"Successfully loaded {len(catalog.services)} service(s).")
            
            # Run basic validation
            validation_errors = catalog.validate_catalog()
            if validation_errors:
                print("\nValidation Errors Found:")
                for error in validation_errors:
                    print(f"- {error}")
            else:
                print("\nBasic validation successful.")
            
            # Run ID format validation if requested
            if args.check_ids:
                id_errors = catalog.validate_ids()
                if id_errors:
                    print("\nID Format Errors Found:")
                    for error in id_errors:
                        print(f"- {error}")
                else:
                    print("ID format validation successful.")
                    
        except Exception as e:
            print(f"Error processing XML: {e}")
            sys.exit(1)
            
    elif args.command == "convert":
        xml_path = args.xml
        output_path = args.output
        output_format = args.format
        
        print(f"Loading service catalog from: {xml_path}")
        try:
            catalog.load_from_xml(xml_path)
            print(f"Successfully loaded {len(catalog.services)} service(s).")
            
            if output_format == "json":
                print(f"Converting to JSON and saving to: {output_path}")
                catalog.export_to_json(output_path)
                print("Conversion complete.")
            elif output_format == "csv":
                print(f"Converting to CSV files and saving to directory: {output_path}")
                csv_files = catalog.export_to_csv(output_path)
                print("Conversion complete. Generated files:")
                for file_type, file_path in csv_files.items():
                    print(f"- {file_type}: {file_path}")
                    
        except Exception as e:
            print(f"Error during conversion: {e}")
            sys.exit(1)
            
    elif args.command == "report":
        xml_path = args.xml
        report_type = args.type
        output_path = args.output
        
        print(f"Loading service catalog from: {xml_path}")
        try:
            catalog.load_from_xml(xml_path)
            print(f"Successfully loaded {len(catalog.services)} service(s).")
            
            if report_type == "summary":
                report = {
                    "total_services": len(catalog.services),
                    "services": [
                        {
                            "id": service.metadata.id,
                            "name": service.metadata.name,
                            "packages": len(service.offering.packages),
                            "retainers": len(service.offering.retainers)
                        }
                        for service in catalog.services
                    ]
                }
            elif report_type == "prices":
                report = catalog.get_price_summary()
            elif report_type == "full":
                report = catalog.generate_service_report()
                
            # Print report summary
            import json
            print("\nReport Summary:")
            print(json.dumps(report, indent=2))
            
            # Save to file if requested
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2)
                print(f"Report saved to: {output_path}")
                
        except Exception as e:
            print(f"Error generating report: {e}")
            sys.exit(1)
            
    elif args.command == "visualize":
        xml_path = args.xml
        viz_type = args.type
        output_path = args.output
        
        print(f"Loading service catalog from: {xml_path}")
        try:
            catalog.load_from_xml(xml_path)
            print(f"Successfully loaded {len(catalog.services)} service(s).")
            
            if viz_type == "prices":
                result = catalog.generate_price_chart(output_path)
                print(f"Price chart generated: {result}")
            elif viz_type == "categories":
                result = catalog.generate_category_chart(output_path)
                print(f"Category chart generated: {result}")
            elif viz_type == "d3":
                catalog.export_for_d3(output_path)
                print(f"D3.js visualization data exported to: {output_path}")
                
        except Exception as e:
            print(f"Error generating visualization: {e}")
            sys.exit(1)
            
    elif args.command == "crud":
        xml_path = args.xml
        operation = args.operation
        service_id = args.service_id
        json_input = args.json_input
        output_xml = args.output
        
        print(f"Loading service catalog from: {xml_path}")
        try:
            catalog.load_from_xml(xml_path)
            print(f"Successfully loaded {len(catalog.services)} service(s).")
            
            if operation == "list":
                print("\nAvailable Services:")
                for service in catalog.services:
                    print(f"ID: {service.metadata.id}, Name: {service.metadata.name}")
                    print(f"  Packages: {len(service.offering.packages)}")
                    print(f"  Retainers: {len(service.offering.retainers)}")
                    print()
                    
            elif operation == "get":
                if not service_id:
                    print("Error: --service-id is required for 'get' operation")
                    sys.exit(1)
                    
                service = catalog.get_service_by_id(service_id)
                if service:
                    print(f"\nService Details (ID: {service_id}):")
                    print(f"Name: {service.metadata.name}")
                    print(f"Category: {service.metadata.category}")
                    print(f"Description: {service.metadata.description}")
                    print(f"Keywords: {', '.join(service.metadata.keywords)}")
                    print(f"Provider: {service.provider.name}")
                    
                    if service.offering.packages:
                        print("\nPackages:")
                        for pkg in service.offering.packages:
                            print(f"  - {pkg.id}: {pkg.name}")
                            
                    if service.offering.retainers:
                        print("\nRetainers:")
                        for ret in service.offering.retainers:
                            print(f"  - {ret.id}: {ret.name}")
                else:
                    print(f"Service with ID '{service_id}' not found.")
                    
            elif operation in ["add", "update"]:
                if not json_input:
                    print(f"Error: --json-input is required for '{operation}' operation")
                    sys.exit(1)
                    
                if not output_xml:
                    print(f"Error: --output is required for '{operation}' operation")
                    sys.exit(1)
                    
                # For demonstration purposes; in a real implementation, this would 
                # parse the JSON and create/update a Service object
                print(f"Operation '{operation}' not fully implemented in this example.")
                print("It would parse the JSON input and create/update a Service object.")
                
            elif operation == "delete":
                if not service_id:
                    print("Error: --service-id is required for 'delete' operation")
                    sys.exit(1)
                    
                if not output_xml:
                    print("Error: --output is required for 'delete' operation")
                    sys.exit(1)
                    
                result = catalog.delete_service(service_id)
                if result:
                    print(f"Service with ID '{service_id}' deleted.")
                    catalog.save_to_xml(output_xml)
                    print(f"Updated catalog saved to: {output_xml}")
                else:
                    print(f"Service with ID '{service_id}' not found.")
                    
        except Exception as e:
            print(f"Error during CRUD operation: {e}")
            sys.exit(1)
            
    else:
        # If no command provided or invalid command
        parser.print_help() 