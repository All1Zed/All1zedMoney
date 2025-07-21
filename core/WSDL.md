🧩 Available services and operations:

📌 Service: KonikWsService
  ↳ Port: KonikWsPort
    📄 Operations (methods):
     🔹 checkCashOutCodeStatus(cashOutCode: xsd:string, customerMobile: xsd:string)
     🔹 generateCashOutCode(customerName: xsd:string, customerSurname: xsd:string, cashOutAmount: xsd:decimal, transactionReference: xsd:string, customerMobile: xsd:string, customerAccountID: xsd:string)
     🔹 getAccountBalance()
     🔹 getAvailableCashDepositIssuers()
     🔹 getBillCustomerName(serviceProvider: xsd:string, billPaymentAccountNumber: xsd:string)
     🔹 getBillPaymentBalanceDue(serviceProvider: xsd:string, billPaymentAccountNumber: xsd:string)
     🔹 getDistributionChannels()
     🔹 getLastVouchersPurchased(serviceProvider: xsd:string, billPaymentAccountNumber: xsd:string, countOfVouchers: xsd:int)
     🔹 getPRNData(prn: xsd:string)
     🔹 getPRNReceipt(prn: xsd:string)
     🔹 getServiceProviderVouchersWithUnits(serviceProvider: xsd:string)
     🔹 getVouchers()
     🔹 getVouchersWithUnits()
     🔹 loadCollection(customerMSISDN: xsd:string, paymentReference: xsd:string, paymentTimeStamp: xsd:dateTime, paymentAmount: xsd:double, paymentChannel: xsd:string)
     🔹 processBankToWallet(transactionAmount: xsd:double, customerAccount: xsd:string, issuerName: xsd:string, bankToWalletReference: xsd:string, transferReference: xsd:string)
     🔹 processCashDeposit(transactionAmount: xsd:double, customerAccount: xsd:string, issuerName: xsd:string, depositorReference: xsd:string)
     🔹 processCashOut(cashOutCode: xsd:string, customerMobile: xsd:string, cashierID: xsd:int)
     🔹 processCustomerPayment(transactionAmount: xsd:double, customerMobile: xsd:string, paymentReference: xsd:string)
     🔹 processZRAPayment(prn: xsd:string, customerMobile: xsd:string, paymentReference: xsd:string)
     🔹 purchaseVoucher(Voucher: ns0:voucherPurchaseRequestWs)
     🔹 purchaseZescoVoucher(Voucher: ns0:voucherPurchaseRequestWs)
     🔹 queryCustomerPayment(paymentReference: xsd:string)
     🔹 queryTransactionStatus(transactionReference: xsd:string)
     🔹 queryZescoTransactionStatus(transactionReference: xsd:string)
     🔹 reconcile()
     🔹 reverseCollection(paymentReference: xsd:string, paymentAmount: xsd:double)
     🔹 reverseCustomerPayment(paymentReference: xsd:string)
     🔹 validateVoucherPurchase(Voucher: ns0:voucherPurchaseRequestWs)

