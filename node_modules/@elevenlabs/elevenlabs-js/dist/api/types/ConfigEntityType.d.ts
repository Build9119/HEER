/**
 * Entity types for the API configuration.
 *
 * This enum contains all valid entity type configurations that users can specify:
 * - Parent types (e.g., "name", "financial_id") that expand to all subtypes
 * - Specific subtypes using dot notation (e.g., "name.full_name")
 * - Standalone terminal types (e.g., "email_address")
 *
 * When converted for service use, parent types expand to all their terminal subtypes.
 */
export declare const ConfigEntityType: {
    readonly Name: "name";
    readonly NameNameGiven: "name.name_given";
    readonly NameNameFamily: "name.name_family";
    readonly NameNameOther: "name.name_other";
    readonly EmailAddress: "email_address";
    readonly ContactNumber: "contact_number";
    readonly Dob: "dob";
    readonly Age: "age";
    readonly ReligiousBelief: "religious_belief";
    readonly PoliticalOpinion: "political_opinion";
    readonly SexualOrientation: "sexual_orientation";
    readonly EthnicityRace: "ethnicity_race";
    readonly MaritalStatus: "marital_status";
    readonly Occupation: "occupation";
    readonly PhysicalAttribute: "physical_attribute";
    readonly Language: "language";
    readonly Username: "username";
    readonly Password: "password";
    readonly Url: "url";
    readonly Organization: "organization";
    readonly FinancialId: "financial_id";
    readonly FinancialIdPaymentCard: "financial_id.payment_card";
    readonly FinancialIdPaymentCardPaymentCardNumber: "financial_id.payment_card.payment_card_number";
    readonly FinancialIdPaymentCardPaymentCardExpirationDate: "financial_id.payment_card.payment_card_expiration_date";
    readonly FinancialIdPaymentCardPaymentCardCvv: "financial_id.payment_card.payment_card_cvv";
    readonly FinancialIdBankAccount: "financial_id.bank_account";
    readonly FinancialIdBankAccountBankAccountNumber: "financial_id.bank_account.bank_account_number";
    readonly FinancialIdBankAccountBankRoutingNumber: "financial_id.bank_account.bank_routing_number";
    readonly FinancialIdBankAccountSwiftBicCode: "financial_id.bank_account.swift_bic_code";
    readonly FinancialIdFinancialIdOther: "financial_id.financial_id_other";
    readonly Location: "location";
    readonly LocationLocationAddress: "location.location_address";
    readonly LocationLocationCity: "location.location_city";
    readonly LocationLocationPostalCode: "location.location_postal_code";
    readonly LocationLocationCoordinate: "location.location_coordinate";
    readonly LocationLocationState: "location.location_state";
    readonly LocationLocationCountry: "location.location_country";
    readonly LocationLocationOther: "location.location_other";
    readonly Date: "date";
    readonly DateInterval: "date_interval";
    readonly UniqueId: "unique_id";
    readonly UniqueIdGovernmentIssuedId: "unique_id.government_issued_id";
    readonly UniqueIdAccountNumber: "unique_id.account_number";
    readonly UniqueIdVehicleId: "unique_id.vehicle_id";
    readonly UniqueIdHealthcareNumber: "unique_id.healthcare_number";
    readonly UniqueIdHealthcareNumberMedicalRecordNumber: "unique_id.healthcare_number.medical_record_number";
    readonly UniqueIdHealthcareNumberHealthPlanBeneficiaryNumber: "unique_id.healthcare_number.health_plan_beneficiary_number";
    readonly UniqueIdDeviceId: "unique_id.device_id";
    readonly UniqueIdUniqueIdOther: "unique_id.unique_id_other";
    readonly Medical: "medical";
    readonly MedicalMedicalCondition: "medical.medical_condition";
    readonly MedicalMedication: "medical.medication";
    readonly MedicalMedicalProcedure: "medical.medical_procedure";
    readonly MedicalMedicalMeasurement: "medical.medical_measurement";
    readonly MedicalMedicalOther: "medical.medical_other";
};
export type ConfigEntityType = (typeof ConfigEntityType)[keyof typeof ConfigEntityType];
