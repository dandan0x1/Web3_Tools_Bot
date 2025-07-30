const { Ed25519Keypair } = require("@mysten/sui/keypairs/ed25519");
const { isValidSuiAddress } = require("@mysten/sui/utils");
const fs = require("fs");
const readline = require("readline");
const inquirer = require("inquirer");
const chalk = require("chalk");

/**
 * SUI 钱包信息类型定义
 * @typedef {Object} SuiWalletInfo
 * @property {string} address - 钱包地址
 * @property {string} privateKey - 私钥
 * @property {string} publicKey - 公钥
 */

class SuiWalletGenerator {
  /**
   * 生成 SUI 钱包
   * @returns {SuiWalletInfo} 钱包信息
   */
  static generateSuiWallet() {
    try {
      // 使用 generate 静态方法创建新的密钥对
      const keypair = Ed25519Keypair.generate();

      return {
        address: keypair.getPublicKey().toSuiAddress(),
        // 获取私钥，这是 suiprivkey 格式，可直接导入到 SUI 钱包
        privateKey: keypair.getSecretKey(),
        // 获取公钥
        publicKey: keypair.getPublicKey().toBase64(),
      };
    } catch (error) {
      throw new Error(`生成SUI钱包失败: ${error.message}`);
    }
  }



  /**
   * 批量生成 SUI 钱包
   * @param {number} count - 需要生成的钱包数量
   * @returns {Promise<Array<SuiWalletInfo>>} SUI 钱包信息数组
   */
  static async generateMultipleSuiWallets(count = 1) {
    const wallets = [];
    let successCount = 0;
    let errorCount = 0;

    console.log(chalk.blue(`开始生成 ${count} 个 SUI 钱包...`));

    for (let i = 0; i < count; i++) {
      try {
        const wallet = this.generateSuiWallet();
        wallets.push(wallet);
        successCount++;
        console.log(chalk.green(`✓ 钱包 ${i + 1} 生成成功: ${wallet.address}`));
      } catch (error) {
        console.error(chalk.red(`✗ 钱包 ${i + 1} 生成失败: ${error.message}`));
        errorCount++;
        wallets.push({
          address: "生成失败",
          privateKey: "生成失败",
          publicKey: "生成失败",
          error: error.message,
        });
      }
    }

    console.log(
      chalk.blue(
        `SUI 钱包生成完成! 成功: ${successCount}, 失败: ${errorCount}`
      )
    );
    return wallets;
  }

  /**
   * 验证 SUI 钱包地址格式
   * @param {string} address - 钱包地址
   * @returns {boolean} 是否有效
   */
  static validateSuiAddress(address) {
    try {
      return isValidSuiAddress(address);
    } catch (error) {
      return false;
    }
  }

  /**
   * 备份现有文件
   * @param {string} walletsDir - 钱包目录
   */
  static backupExistingFiles(walletsDir) {
    const files = ['sui_addresses.txt', 'sui_keys.txt', 'sui_public_keys.txt'];
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
    const backupDir = `${walletsDir}/backup_${timestamp}`;
    
    try {
      // 创建备份目录
      if (!fs.existsSync(backupDir)) {
        fs.mkdirSync(backupDir, { recursive: true });
      }
      
      let backupCount = 0;
      files.forEach(file => {
        const filePath = `${walletsDir}/${file}`;
        if (fs.existsSync(filePath)) {
          const backupPath = `${backupDir}/${file}`;
          fs.copyFileSync(filePath, backupPath);
          backupCount++;
        }
      });
      
      if (backupCount > 0) {
        console.log(chalk.yellow(`✓ 已备份 ${backupCount} 个文件到: ${backupDir}`));
      }
    } catch (error) {
      console.log(chalk.red("备份文件失败:", error.message));
    }
  }

  /**
   * 将 SUI 钱包信息保存到文件
   * @param {Array<SuiWalletInfo>} wallets - 钱包信息数组
   */
  static saveSuiWalletsToFiles(wallets) {
    try {
      let addressContent = "=============== SUI Addresses ===============\n\n";
      let privateKeyContent = "=============== SUI Private Keys ===============\n\n";
      let publicKeyContent = "=============== SUI Public Keys ===============\n\n";

      wallets.forEach((wallet) => {
        // 跳过生成失败的钱包
        if (wallet.address === "生成失败") return;
        
        addressContent += `${wallet.address}\n`;
        privateKeyContent += `${wallet.privateKey}\n`;
        publicKeyContent += `${wallet.publicKey}\n`;
      });

      // 创建 wallets 目录（如果不存在）
      const walletsDir = "wallets";
      if (!fs.existsSync(walletsDir)) {
        fs.mkdirSync(walletsDir, { recursive: true });
      }

      // 备份现有文件
      this.backupExistingFiles(walletsDir);

      // 保存到 wallets 目录下的不同文件
      fs.writeFileSync(`${walletsDir}/sui_addresses.txt`, addressContent);
      fs.writeFileSync(`${walletsDir}/sui_keys.txt`, privateKeyContent);
      fs.writeFileSync(`${walletsDir}/sui_public_keys.txt`, publicKeyContent);

      console.log(chalk.blue("SUI 钱包信息已保存到以下文件："));
      console.log(chalk.blue(`- ${walletsDir}/sui_addresses.txt (地址)`));
      console.log(chalk.blue(`- ${walletsDir}/sui_keys.txt (私钥)`));
      console.log(chalk.blue(`- ${walletsDir}/sui_public_keys.txt (公钥)`));
    } catch (error) {
      console.log(chalk.red("保存 SUI 钱包信息失败:", error));
    }
  }

  /**
   * 显示钱包信息
   * @param {SuiWalletInfo} wallet - 钱包信息
   * @param {number} index - 钱包索引
   */
  static displayWallet(wallet, index = 1) {
    console.log(chalk.cyan(`\n=== SUI 钱包 ${index} ===`));
    console.log(chalk.white(`地址: ${wallet.address}`));
    console.log(chalk.white(`私钥: ${wallet.privateKey}`));
    console.log(chalk.white(`公钥: ${wallet.publicKey}`));
  }

  /**
   * 显示所有钱包信息
   * @param {Array<SuiWalletInfo>} wallets - 钱包信息数组
   */
  static displayAllWallets(wallets) {
    console.log(chalk.cyan("\n=== 生成的 SUI 钱包信息 ==="));
    wallets.forEach((wallet, index) => {
      if (wallet.address !== "生成失败") {
        this.displayWallet(wallet, index + 1);
      }
    });
  }
}

/**
 * 命令行交互函数
 * @returns {Promise<{count: number}>}
 */
async function promptUser() {
  try {
    // 输入钱包数量
    const countAnswer = await inquirer.prompt([
      {
        type: "input",
        name: "count",
        message: "请输入要生成的 SUI 钱包数量:",
        validate: (value) => {
          const numValue = parseInt(value, 10);
          const valid = !isNaN(numValue) && numValue > 0 && Number.isInteger(numValue);
          return valid || "请输入有效的正整数";
        },
        filter: (value) => {
          const numValue = parseInt(value, 10);
          return !isNaN(numValue) && numValue > 0 && Number.isInteger(numValue)
            ? numValue
            : "";
        },
      },
    ]);

    return {
      count: parseInt(countAnswer.count, 10),
    };
  } catch (error) {
    throw error;
  }
}

const COLORS = {
  GREEN: '\x1b[32m',
  YELLOW: '\x1b[33m',
  RED: '\x1b[31m',
  WHITE: '\x1b[37m',
  GRAY: '\x1b[90m',
  CYAN: '\x1b[36m',
  RESET: '\x1b[0m'
};

/**
 * 主函数
 */
async function main() {
  try {
    // console.log(chalk.cyan("=== SUI 钱包生成器 ==="));
    // 显示版权信息
    console.log(COLORS.GREEN + `*****************************************************` + COLORS.RESET);
    console.log(COLORS.CYAN + `*           X:` + COLORS.YELLOW + ` https://x.com/ariel_sands_dan         ` + COLORS.CYAN + `*` + COLORS.RESET);
    console.log(COLORS.CYAN + `*           Tg:` + COLORS.YELLOW + ` https://t.me/sands0x1                ` + COLORS.CYAN + `*` + COLORS.RESET);
    console.log(COLORS.CYAN + `*           ` + COLORS.RED + `SUI 钱包生成器 Version 1.0               ` + COLORS.CYAN + `*` + COLORS.RESET);
    console.log(COLORS.CYAN + `*           ` + COLORS.GRAY + `Copyright (c) 2025                       ` + COLORS.CYAN + `*` + COLORS.RESET);
    console.log(COLORS.CYAN + `*           ` + COLORS.GRAY + `All Rights Reserved                      ` + COLORS.CYAN + `*` + COLORS.RESET);
    console.log(COLORS.GREEN + `*****************************************************` + COLORS.RESET);
    console.log(`${'='.repeat(50)}`);
    console.log(chalk.cyan('申请key: https://661100.xyz/'));
    console.log(chalk.cyan('联系Dandan: \n QQ:712987787 QQ群:1036105927 \n 电报:sands0x1 电报群:https://t.me/+fjDjBiKrzOw2NmJl \n 微信: dandan0x1'));
    console.log(`${'='.repeat(50)}`);
    // 获取用户输入
    const userInput = await promptUser();

    console.log(
      chalk.green(`\n开始生成 ${userInput.count} 个 SUI 钱包...`)
    );

    // 生成钱包
    const wallets = await SuiWalletGenerator.generateMultipleSuiWallets(userInput.count);

    // 显示钱包信息
    SuiWalletGenerator.displayAllWallets(wallets);

    // 保存到文件
    SuiWalletGenerator.saveSuiWalletsToFiles(wallets);

    console.log(chalk.green("\nSUI 钱包生成完成！"));
  } catch (error) {
    console.error(chalk.red("错误:", error.message));
    process.exit(1);
  }
}

// 如果直接运行此文件，则执行main函数
if (require.main === module) {
  main();
}

// 导出类和函数
module.exports = {
  SuiWalletGenerator,
  main,
}; 
