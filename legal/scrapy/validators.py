from crawl.scrapy.validators import *
import re

from schematics.types.compound import ListType, ModelType
from schematics.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator

class PersonInfo(Model):
    firstName = StringType()
    lastName = StringType()
    middleInitial = StringType()
    
class CasesAgainstDoctors(BaseSchemaItem):
    name = 'dea_meta'    
    dataFileYear = StringType(max_length=4,required=True)
    caseYearURL = StringType(required=True) 
    involvedCaseEntityType = StringType()
    individualPersonType = StringType()
    personTypeAcronym = StringType()
    personName =  ModelType(PersonInfo)
    businessName = StringType()
    typeofCase = StringType()
    casePostDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    caseRecordFileURL = StringType(required=True)
    federalRegisterReference = StringType() 
    federalRegisterPostDate = DateTimeType(serialized_format='%m/%d/%Y') 
    federalRegisterDocumentNumber = StringType()
    caseSummary = StringType()
    findingsofFact = StringType()
    sanctions = StringType()
    order_info = StringType()
    federalRegisterFileDate = DateTimeType(serialized_format='%m/%d/%Y')
    federalRegisterFileTime = StringType()#input_formats=('%H:%M'))
    lastRecordDataStatus    = StringType()
    administrativeAuthority = DictType(StringType)
    federalRegisterPages    = StringType()
    billingCode             = StringType()
    additionalInfo          = DictType(StringType)
    

    '''def validate_entity_type(self,data):
	if data['PersonTypeAcronym'] and data['IndividualPersonType'] != '':
	    raise ValidationError('if persontype acronym  present, the IndividualPersonType should not be empty')
        if data['InvolvedCaseEntityType'] == 'Business Entity'  and data['BusinessName'] != '' and data['PersonTypeAcronym'] == '':
	    raise ValidationError('InvolvedCaseEntityType is business entity type then business should not be empty')'''

class OutofstateDisciplineschema(BaseSchemaItem):
    date = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    state = StringType()
    selectedstateLicenseNumber = StringType()
    actions = StringType()
    comment = StringType()

class MassachusettsBoardDisciplineschema(BaseSchemaItem):
    date = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    action = StringType()
    caseNumber = StringType()
    instrument = StringType()
    cost = FloatType()
    actionNote = StringType()
    fineAmount = StringType()

class HealthCareFacilityDiscipline(BaseSchemaItem):
    facility = StringType()
    facilityType = StringType()
    actionBeginDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    actionEndDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    action = StringType()
    basisorAllegation = StringType()

class massachusettsCriminalConvictionsschema(BaseSchemaItem):
     charge  = StringType()
     court = StringType()
     jurisdiction = StringType()
     disposition = StringType()
     dispositionDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
     docketNumber = StringType()
     conviction = StringType()
     sentence = StringType()

class Massachusettsmalpracticeclaimsschema(BaseSchemaItem):
    speciality = StringType()
    date = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    categoryofPayment  = StringType()
    
class MassachusettsmalboardCertificationsschema(BaseSchemaItem):
    boardName = StringType()
    generalCertification  = StringType()
    subspecialty = StringType()
    abmsBoardCertification = BooleanType()
    aoaboardCertification = BooleanType()

class BusinessAddressschema(BaseSchemaItem):
    address = StringType()
    city = StringType()
    state = StringType()
    zip_code = StringType()
    country = StringType()

class Massachusetts(BaseSchemaItem):
    name = 'massachusetts_meta'
    personName =  ModelType(PersonInfo)
    licenseNumber = IntType(required=True)
    licenseStatus = StringType(required=True)
    expireDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    outofstateDiscipline = ListType(ModelType(OutofstateDisciplineschema))
    boarddiscipline = ListType(ModelType(MassachusettsBoardDisciplineschema))
    healthcarefacilityDiscipline = ListType(ModelType(HealthCareFacilityDiscipline))
    criminalConvictions = ListType(ModelType(massachusettsCriminalConvictionsschema))
    malpracticeclaims = ListType(ModelType(Massachusettsmalpracticeclaimsschema))
    professionalPublications = ListType(StringType)
    honorsandAwards = ListType(StringType)
    boardCertifications = ListType(ModelType(MassachusettsmalboardCertificationsschema))
    areaofSpecialty = StringType()
    designation = StringType()
    primaryWorkSetting = StringType()
    businessAddress = ListType(ModelType(BusinessAddressschema))
    businessTelephone = StringType()
    acceptingNewPatients = StringType(max_length=1)
    acceptsMedicaid =  StringType(max_length=1)
    translationServicesAvailable = StringType()
    insuranceplansAccepted = StringType()
    hospitalAffiliations = StringType()
    npiNumber = StringType()
    medicalSchool = StringType()
    graduationDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    postGraduateTraining  = ListType(StringType)
    licenseIssueDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    retiredDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    resignedDate  = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    vanpDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    summarySuspensionDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    suspensionDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    revocationDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    renewalDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    additionalInfo = DictType(StringType)
    
class Specialtyschema(Model):
    certifyingBoard = StringType()
    specialty = StringType()

class MedicalSchoolFacultiesschema(Model):
    school_name = StringType()
    position = StringType()

class Hospitalprivilegsschema(Model):
    hospitalName = StringType(required=True)
    city = StringType()
    zip_code = StringType()
    state_code = StringType()

class CriminalOffensesschema(Model):
    dateofOffense  = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    jurisdiction = StringType()
    descriptionofOffense  = StringType()

class Awardsschema(Model):
    name = StringType()
    organization = StringType()

class Malpraticeamountschema(Model):
    date = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    ammount = StringType()

class DisciplinaryActionschema(Model):
     actionAgency = StringType()
     actionDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
     violationdescription = StringType()
     actionType = StringType()
     actionDescription = StringType()

class PrivilegeRevocationsschema(Model):
    hospitalName = StringType()
    revocationDate  = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    violationDescription = StringType()
    actionType = StringType()
    actionDescription = StringType()

class EducationInfoschema(Model):
    schoolType = StringType()
    fromDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    toDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    graduated = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    schoolName = StringType()

class MedicalEducationInfoschema(Model):
    programType = StringType()
    hospitalName = StringType()
    fromDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    toDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    address = StringType()
    country = StringType()
    graduated = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')

class RelatedLicensesschema(Model):
    relationship = StringType()
    name = StringType()
    sinceDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    endDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    licenseType = StringType()
    licenseNumber = StringType()
    status = StringType()

class CurrentPracticeLocationschema(Model):
    city = StringType()
    state = StringType()
    country = StringType()
    fromDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    toDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')

class MembershipInProfessionalOrganizationsschema(Model):
    organization = StringType()
    organizationType = StringType()
    description = StringType()

class PublicDocumentsschema(Model):
    documentURL = StringType()
    documentType = StringType()

class GeorgiaSchema(BaseSchemaItem):
    name = 'georgia_meta'
    firstName = StringType()
    middleName = StringType()
    lastName = StringType()
    suffix = StringType()
    licenseType = StringType()
    designation  = StringType()
    status = StringType()
    licenseNumber = StringType(required=True)
    profession = StringType(required=True)
    professionSubtype = StringType()
    licenseIssueDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    licenseExpiryDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    licenseRenewalDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    primarySpecialty = ListType(ModelType(Specialtyschema))
    streetAddress = StringType()
    zip_code = StringType()
    state = StringType()
    country = StringType()
    county = StringType()
    relatedLicenses = ListType(ModelType(RelatedLicensesschema))
    publicDocuments = ListType(ModelType(PublicDocumentsschema))
    profileSubmissionDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    initialLicensureState = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    initialLicenseIssueDate = DateTimeType(serialized_format='%Y-%m-%d %H:%M:%S')
    malpracticeCoverage = StringType()
    currentPracticeLocation = ListType(ModelType(CurrentPracticeLocationschema))
    acceptingMedicaidPatients = StringType(max_length = 1) # Y/N
    acceptingMedicarePatients = StringType(max_length = 1) # Y/N
    # graduationYearfromCollege = StringType()
    # universityName = StringType()
    educationInfo = ListType(ModelType(EducationInfoschema))
    medicalEducationInfo = ListType(ModelType(MedicalEducationInfoschema))
    currentHospitalPrivileges = ListType(ModelType(Hospitalprivilegsschema))
    disciplinaryAction  = ListType(ModelType(DisciplinaryActionschema))
    privilegeRevocations  = ListType(ModelType(PrivilegeRevocationsschema))
    criminalOffensesStatus = ListType(ModelType(CriminalOffensesschema))
    arbitrationAwards = ListType(ModelType(Malpraticeamountschema))
    settlementAmounts = ListType(ModelType(Malpraticeamountschema))
    membershipInOrganizations = ListType(ModelType(MembershipInProfessionalOrganizationsschema))
    awards = ListType(ModelType(Awardsschema))
    medicalSchoolFaculties    = ListType(ModelType(MedicalSchoolFacultiesschema))




